require 'bible_parser'
require 'bible_ref'
require 'sequel'

class BibleImporter
  BOOK_IDS = { 'SOS' => 'SNG', 'JOE' => 'JOL', 'EZE' => 'EZK', 'NAH' => 'NAM' }.freeze
  LICENSE_CREDITS = {
    'bes' => '© 2018 AudioBiblia.org / Irma Flores',
    'pddpt' => '© 2017–2022 Asociacion Biblica Latinoamericana',
    'vbl' => '© 2018–2020 Jonathan Gallagher y Shelly Barrios de Avila',
  }.freeze

  def self.translations(directory)
    readme = File.read(File.join(directory, 'README.md'))
    lines = readme.lines.grep(/^\|/)
    headings = lines.shift.split('|')[1...-1].map { |cell| cell.strip.downcase }
    links = readme.scan(/^\[([^\]]+)\]:\s*(\S+)/).to_h
    lines
      .drop(1)
      .map do |line|
        row = headings.zip(line.split('|')[1...-1].map(&:strip)).to_h
        filename = row.fetch('filename')
        language, *parts = filename.split('.').first.split('-')
        identifier = parts.length == 1 ? parts.first : row.fetch('abbrev').downcase
        if language == 'chi'
          simplified = parts.include?('simp')
          language = simplified ? 'zh-cn' : 'zh-tw'
          identifier = simplified ? 'cuv-simp' : 'cuv'
        end
        raise "Missing identifier for #{filename}" if identifier.to_s.empty?

        license = row.fetch('license').gsub(/\[([^\]]+)\]\[([^\]]+)\]/) { "#{$1} (#{links.fetch($2)})" }
        license = 'See https://github.com/seven1m/open-bibles#hebrew-leningrad-codex' if license == '_see below_'
        license += "; #{LICENSE_CREDITS[identifier]}" if LICENSE_CREDITS.key?(identifier)
        {
          filename: filename,
          identifier: identifier,
          name: row.fetch('version'),
          language: row.fetch('language'),
          language_code: language,
          license: license,
        }
      end
  end

  def initialize(db, output: $stdout)
    @db = db
    @output = output
  end

  def each_verse(path, translation)
    return enum_for(__method__, path, translation) unless block_given?

    language = BibleRef::LANGUAGES.fetch(translation.fetch(:language_code)).new
    books = language.books
    references = {}
    count = 0
    File.open(path) do |file|
      bible = BibleParser.new(file)
      fragments = bible.format == 'OSIS' ? osis_fragments(file) : {}
      chapter_rows = []
      chapter_key = nil
      bible.each_verse do |verse|
        data = verse.to_h
        book_id = BOOK_IDS.fetch(data[:book_id], data[:book_id])
        book = books[book_id]&.fetch(:name) || data[:book_title]
        raise "Unknown book #{book_id.inspect} in #{path}" if book.to_s.empty?
        chapter = data.delete(:chapter_num)
        number = data.delete(:num)
        unless chapter.to_i.positive? && number.to_i.positive?
          raise "Invalid reference in #{path}: #{book_id} #{chapter}:#{number}"
        end

        reference = [book_id, chapter, number]
        next if references[reference] && fragments.key?(reference)
        raise "Duplicate reference in #{path}: #{reference.join('.')}" if references[reference]
        references[reference] = true
        data.delete(:book_title)
        if chapter_key && chapter_key != [book_id, chapter]
          chapter_rows.sort_by { |row| row[:verse] }.each { |row| yield row }
          chapter_rows.clear
        end
        chapter_key = [book_id, chapter]
        data[:text] = fragments[reference] if fragments.key?(reference)
        data[:text] = data[:text].gsub(/\A[[:space:]]+|[[:space:]]+\z/, '')
        chapter_rows << data.merge(book_id: book_id, book: book, chapter: chapter, verse: number)
        count += 1
      end
      chapter_rows.sort_by { |row| row[:verse] }.each { |row| yield row }
    end
    raise "No verses found in #{path}" if count.zero?
    count
  end

  def import(path, translation, overwrite: false)
    @db.transaction(savepoint: true) do
      existing = @db[:translations].where(identifier: translation.fetch(:identifier))
      if (id = existing.get(:id))
        unless overwrite
          @output.puts '  skipping existing translation (pass --overwrite)'
          next
        end
        @db[:verses].where(translation_id: id).delete
        existing.delete
      end
      id = @db[:translations].insert(translation.reject { |key, _| key == :filename })
      batch = []
      count =
        each_verse(path, translation) do |data|
          batch << data.merge(translation_id: id)
          if batch.size == 1_000
            @db[:verses].multi_insert(batch)
            batch.clear
          end
        end
      @db[:verses].multi_insert(batch) unless batch.empty?
      @output.puts "  imported #{count} verses"
      count
    end
  end

  private

  # Some OSIS sources split a numbered verse into lettered parts, interleaved
  # with other verses. The API stores integer verse numbers, so join those
  # parts in their labelled order before importing the chapter.
  def osis_fragments(file)
    parts = {}
    file.rewind
    Nokogiri::XML
      .Reader(file)
      .each do |node|
        next unless node.node_type == Nokogiri::XML::Reader::TYPE_ELEMENT && node.local_name == 'verse'
        match = node.attribute('osisID')&.match(/\A([^.]+)\.(\d+)\.(\d+)!?([a-z])\z/)
        next unless match

        book = BibleParser::Parsers::OSIS::BookIDs::BOOK_IDS.fetch(match[1])
        document = Nokogiri.XML(node.outer_xml)
        document.xpath('//*[local-name()="note"]').remove
        key = [book, match[2].to_i, match[3].to_i]
        (parts[key] ||= {})[match[4]] = document.root.text
      end
    parts.transform_values { |values| values.sort.map(&:last).join }
  end
end
