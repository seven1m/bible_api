require 'bible_parser'
require 'bible_ref'
require 'bundler/setup'
require 'dotenv'
require 'mysql2'
require 'optparse'
require 'sequel'

Dotenv.load

@options = {
  bibles_path: './bibles'
}

OptionParser.new do |opts|
  opts.banner = 'Usage: ruby import.rb [options]'

  opts.on('-t', '--translation=NAME', 'Only import a single translation (e.g. eng-ylt.osis.xml)') do |name|
    @options[:translation] = name
  end

  opts.on('--bibles-path=PATH', 'Specify custom path for open-bibles (default: #{@options[:bibles_path].inspect})') do |path|
    @options[:bibles_path] = path
  end

  opts.on('--overwrite', 'Overwrite any existing data') do
    @options[:overwrite] = true
  end

  opts.on('--drop-tables', 'Drop all tables first (and recreate them)') do
    @options[:drop_tables] = true
  end

  opts.on('-h', '--help') do
    puts opts
    exit
  end
end.parse!

unless ENV['DATABASE_URL']
  puts 'Must set the DATABASE_URL environment variable (probably in .env)'
  exit 1
end

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

if @options[:drop_tables]
  DB.drop_table :translations
  DB.drop_table :verses
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

# grab bible file info from the README.md table (markdown format)
table = File.read("#{@options[:bibles_path]}/README.md").scan(/^ *\|.+\| *$/)
headings = table.shift.split(/\s*\|\s*/)
table.shift # junk
translations = table.map do |row|
  cells = row.split(/\s*\|\s*/)
  headings.each_with_index.each_with_object({}) do |(heading, index), hash|
    hash[heading.downcase] = cells[index] unless heading.empty?
  end
end

translations.each do |translation|
  path = "#{@options[:bibles_path]}/#{translation['filename']}"
  next if @options[:translation] && path.split('/').last != @options[:translation]

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
    if @options[:overwrite]
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
