require 'bundler/setup'
require_relative 'lib/bible_importer'
require 'dotenv'
require 'mysql2'
require 'optparse'
require 'sequel'

Dotenv.load

@options = { bibles_path: './bibles' }

OptionParser
  .new do |opts|
    opts.banner = 'Usage: ruby import.rb [options]'

    opts.on('-t', '--translation=NAME', 'Only import a single translation (e.g. eng-bsb.usfx.xml)') do |name|
      @options[:translation] = name
    end

    opts.on(
      '--bibles-path=PATH',
      "Specify custom path for open-bibles (default: #{@options[:bibles_path].inspect})",
    ) { |path| @options[:bibles_path] = path }

    opts.on('--overwrite', 'Overwrite any existing data') { @options[:overwrite] = true }

    opts.on('--drop-tables', 'Drop all tables first (and recreate them)') { @options[:drop_tables] = true }

    opts.on('-h', '--help') do
      puts opts
      exit
    end
  end
  .parse!

unless ENV['DATABASE_URL']
  puts 'Must set the DATABASE_URL environment variable (probably in .env)'
  exit 1
end

DB = Sequel.connect(ENV['DATABASE_URL'].sub(%r{mysql://}, 'mysql2://'), encoding: 'utf8mb4')

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

importer = BibleImporter.new(DB)
translations = BibleImporter.translations(@options[:bibles_path])
if @options[:translation]
  translations.select! { |translation| translation[:filename] == @options[:translation] }
  abort "Translation not found: #{@options[:translation]}" if translations.empty?
end

translations.each do |translation|
  path = File.join(@options[:bibles_path], translation.fetch(:filename))
  puts path
  importer.import(path, translation, overwrite: @options[:overwrite])
end
