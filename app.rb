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
      text: verses.map { |v| v[:text] }.join
    }.to_json
  else
    status 404
    { error: 'not found' }.to_json
  end
end
