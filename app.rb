require 'bundler'
require 'json'

Bundler.require

DB = Sequel.connect(ENV['BIBLE_API_DB'])

def get_verse_id(ref)
  record = DB[
    'select id from verses where book_id = ? and chapter = ? and verse = ?',
    ref[:book],
    ref[:chapter],
    ref[:verse]
  ].first
  record ? record[:id] : nil
end

def get_verses(ranges)
  all = []
  ranges.each do |(ref_from, ref_to)|
    start_id = get_verse_id(ref_from)
    stop_id  = get_verse_id(ref_to)
    if start_id and stop_id
      all += DB['select * from verses where id between ? and ?', start_id, stop_id].to_a
    else
      return nil
    end
  end
  all
end

get '/' do
  content_type 'application/json'
  {
    url: 'http://bible-api.com',
    description: 'RESTful API for querying bible passages from the World English Bible.',
    examples: [
      'http://bible-api.com/john 3:16',
      'http://bible-api.com/romans 12:1-2'
    ]
  }.to_json
end

get '/:ref' do
  content_type 'application/json'
  ref_string = params[:ref].gsub(/\+/, ' ')
  ref = BibleRef::Reference.new(ref_string)
  if ranges = ref.ranges
    if verses = get_verses(ranges)
      verses.map! do |v|
        {
          book_id:   v[:book_id],
          book_name: v[:book],
          chapter:   v[:chapter],
          verse:     v[:verse],
          text:      v[:text]
        }
      end
      {
        reference: ref.normalize,
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
  else
    status 404
    { error: 'not found' }.to_json
  end
end
