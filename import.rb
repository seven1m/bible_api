require 'bundler/setup'
require 'sequel'
require 'mysql2'
require 'bible_parser'
require 'bible_ref'

DB = Sequel.connect(ENV['DATABASE_URL'].sub(%r{mysql://}, 'mysql2://'), encoding: 'utf8mb4')

class Importer
  def import(path, translation_id)
    puts '  importing...'
    bible = BibleParser.new(File.open(path))
    bible.each_verse do |verse|
      data = verse.to_h
      data[:book] = data.delete(:book_title)
      data[:chapter] = data.delete(:chapter_num)
      data[:verse] = data.delete(:num)
      data[:translation_id] = translation_id
      print "  #{translation_id} - #{data[:book]} #{data[:chapter]}:#{data[:verse]}                    \r"
      DB[:verses].insert(data)
    end
    puts '  done                                             '
  end
end

if ARGV.delete('--drop-tables')
  DB.drop_table :translations
  DB.drop_table :verses
end

if ARGV.delete('--overwrite')
  @overwrite = true
end

DB.create_table? :translations, charset: 'utf8mb4' do
  primary_key :id
  String :identifier
  String :name
  String :language
  String :language_code
  String :license
end

DB.create_table? :verses, charset: 'utf8mb4' do
  primary_key :id
  Fixnum :book_num
  String :book_id
  String :book
  Fixnum :chapter
  Fixnum :verse
  String :text, text: true
  Fixnum :translation_id
end

importer = Importer.new

BIBLES_PATH = ARGV[0] || 'bibles'
TRANSLATION = ARGV[1] # for debugging

# grab bible file info from the README.md table (markdown format)
table = File.read("#{BIBLES_PATH}/README.md").scan(/^ *\|.+\| *$/)
headings = table.shift.split(/\s*\|\s*/)
table.shift # junk
translations = table.map do |row|
  cells = row.split(/\s*\|\s*/)
  headings.each_with_index.each_with_object({}) do |(heading, index), hash|
    hash[heading.downcase] = cells[index] unless heading.empty?
  end
end

translations.each do |translation|
  path = "#{BIBLES_PATH}/#{translation['filename']}"
  next if TRANSLATION && path.split('/').last != TRANSLATION

  puts path
  lang_code_and_id = translation.delete('filename').split('.').first
  lang_parts = lang_code_and_id.split('-')
  if lang_parts.size == 3
    translation['language_code'] = lang_parts.first
    translation['identifier'] = translation['abbrev'].downcase
    raise 'bad abbrev' if translation['identifier'].to_s.strip == ''
  elsif lang_parts.size == 2
    translation['language_code'], translation['identifier'] = lang_parts
  else
    raise "error with language and id for lang parts: #{lang_parts.inspect}"
  end
  translation['language_code'] = 'zh-tw' if translation['language_code'] == 'chi'
  translation.delete('format')
  translation.delete('abbrev')
  translation['name'] = translation.delete('version')
  language = translation['language_code']
  begin
    BibleRef::Reference.new('John 3:16', language: language)
  rescue KeyError
    puts "  language #{language} not supported"
    next
  end

  existing_id = DB['select id from translations where identifier = ?', translation['identifier']].first&.fetch(:id, nil)
  if existing_id
    if @overwrite
      DB[:verses].where(translation_id: existing_id).delete
      DB[:translations].where(identifier: translation['identifier']).delete
    else
      puts '  skipping existing translation (pass --overwrite)'
      next
    end
  end

  id = DB[:translations].insert(translation)
  importer.import(path, id)
end
