require 'bundler'
require 'json'

Bundler.require

DB = Sequel.connect(ENV['BIBLE_API_DB'])

def get_verse_id(ref)
  DB[
    'select id from verses where book_id = ? and chapter = ? and verse = ?',
    ref[:book],
    ref[:chapter],
    ref[:verse]
  ].first[:id]
end

def get_verses(ranges)
  all = []
  ranges.each do |(ref_from, ref_to)|
    start_id = get_verse_id(ref_from)
    stop_id  = get_verse_id(ref_to)
    all += DB['select * from verses where id between ? and ?', start_id, stop_id].to_a
  end
  all
end

get '/' do
  <<-HTML
    <!doctype html>
    <h1>bible-api.com</h1>
    <p><a href="https://github.com/seven1m/bible_api">github.com/seven1m/bible_api</a></p>
    <p>examples:</p>
    <ul>
      <li><a href="/john%203:16">john 3:16</a></li>
      <li><a href="/romans+12:1-2">romans 12:1-2</a></li>
    </ul>
  HTML
end

get '/:ref' do
  ref = params[:ref].gsub(/\+/, ' ')
  if ranges = BibleRef::Reference.new(ref).ranges
    verses = get_verses(ranges).map do |v|
      {
        book_id:   v[:book_id],
        book_name: v[:book],
        chapter:   v[:chapter],
        verse:     v[:verse],
        text:      v[:text]
      }
    end
    {
      reference: ref,
      verses: verses,
      text: verses.map { |v| v[:text] }.join,
      translation_id: 'WEB',
      translation_name: 'World English Bible',
      translation_note: 'The World English Bible, a Modern English update of the American Standard Version of the Holy Bible, is in the public domain. Copy and publish it freely.'
    }.to_json
  else
    status 404
    { error: 'not found' }.to_json
  end
end
