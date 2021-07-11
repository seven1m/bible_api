require 'bundler/setup'
require 'sequel'
require 'mysql2'
require 'bible_parser'
require 'bible_ref'

DB = Sequel.connect(ENV['BIBLE_API_DB'])

class Importer
  def import(path, translation_id)
    puts path
    bible = BibleParser.new(File.open(path))
    bible.each_verse do |verse|
      data = verse.to_h
      data[:book] = data.delete(:book_title)
      data[:chapter] = data.delete(:chapter_num)
      data[:verse] = data.delete(:num)
      data[:translation_id] = translation_id
      print "#{translation_id} - #{data[:book]} #{data[:chapter]}:#{data[:verse]}                    \r"
      DB[:verses].insert(data)
    end
  end
end

DB.create_table? :translations, charset: 'utf8' do
  primary_key :id
  String :identifier
  String :name
  String :language
  String :language_code
  String :license
end

DB.create_table? :verses, charset: 'utf8' do
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

# grab bible file info from the README.md table (markdown format)
table = File.read('bibles/README.md').scan(/^ *\|.+\| *$/)
headings = table.shift.split(/\s*\|\s*/)
table.shift # junk
translations = table.map do |row|
  cells = row.split(/\s*\|\s*/)
  headings.each_with_index.each_with_object({}) do |(heading, index), hash|
    hash[heading.downcase] = cells[index] unless heading.empty?
  end
end

translations.each do |translation|
  path = "bibles/#{translation['filename']}"
  lang_code_and_id = translation.delete('filename').split('.').first
  lang_parts = lang_code_and_id.split('-')
  if lang_parts.size == 3
    translation['language_code'] = lang_parts.first
    translation['identifier'] = translation['abbrev'].downcase
    raise 'bad abbrev' if translation['identifier'].to_s.strip == ''
  elsif lang_parts.size == 2
    translation['language_code'], translation['identifier'] = lang_parts
  else
    raise 'error with language and id'
  end
  translation.delete('format')
  translation.delete('abbrev')
  translation['name'] = translation.delete('version')
  begin
    BibleRef::Reference.new('John 3:16', language: translation['language_code'].split('-').first)
  rescue KeyError
    next # languaged not supported
  end
  unless DB['select id from translations where identifier = ?', translation['identifier']].any?
    id = DB[:translations].insert(translation)
    importer.import(path, id)
  end
end
