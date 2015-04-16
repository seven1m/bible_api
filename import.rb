require 'bundler/setup'
require 'sequel'
require 'mysql2'
require 'usfx'

DB = Sequel.connect(ENV['BIBLE_API_DB'])

class Importer
  class VerseDocument < USFX::Document
    def initialize(translation_id)
      super()
      @translation_id = translation_id
    end

    def verse(data)
      data[:book].strip!
      data[:translation_id] = @translation_id
      print "#{@translation_id} - #{data[:book]} #{data[:chapter]}:#{data[:verse]}                    \r"
      DB[:verses].insert(data)
    end
  end

  def import(translation, path)
    parser = USFX::Parser.new(VerseDocument.new(translation))
    parser.parse(File.open(path))
  end
end

DB.create_table :translations do
  primary_key :id
  String :identifier
  String :name
  String :license
end

DB.create_table :verses do
  primary_key :id
  Fixnum :book_num
  String :book_id
  String :book
  Fixnum :chapter
  Fixnum :verse
  String :text
  Fixnum :translation_id
end

importer = Importer.new

TRANSLATIONS = [
  {
    identifier: 'WEB',
    name:       'World English Bible',
    license:    'The World English Bible, a Modern English update of the American Standard Version ' \
                'of the Holy Bible, is in the public domain. Copy and publish it freely.',
    path:       'bibles/eng-web_usfx.xml'
  },
  {
    identifier: 'RCCV',
    name:       'Romanian Corrected Cornilescu Version',
    license:    'Public Domain',
    path:       'bibles/RCCV.USFX.xml'
  }
]

TRANSLATIONS.each do |translation|
  path = translation.delete(:path)
  id = DB[:translations].insert(translation)
  importer.import(id, path)
end
