require 'bundler'
require 'sequel'
require 'mysql2'
require 'usfx'

class Seed
  DB = Sequel.connect(ENV['BIBLE_API_DB'])

  class VerseDocument < USFX::Document
    def verse(data)
      data[:book].strip!
      print "#{data[:book]} #{data[:chapter]}:#{data[:verse]}                    \r"
      DB[:verses].insert(data)
    end
  end

  def import
    DB.create_table :verses do
      primary_key :id
      Fixnum :book_num
      String :book_id
      String :book
      Fixnum :chapter
      Fixnum :verse
      String :text
    end

    if DB[:verses].count > 0
      puts 'data already present'
      exit(1)
    end

    parser = USFX::Parser.new(VerseDocument.new)
    parser.parse(File.open('eng-web_usfx.xml'))
  end
end

Seed.new.import
