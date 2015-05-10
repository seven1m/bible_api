require 'bundler'
require 'json'

Bundler.require

DB = Sequel.connect(ENV['BIBLE_API_DB'], charset: 'utf8')

set :protection, except: [:json_csrf]

def get_verse_id(ref, translation_id)
  record = DB[
    'select id from verses where book_id = ? and chapter = ? and verse = ? and translation_id = ?',
    ref[:book],
    ref[:chapter],
    ref[:verse],
    translation_id
  ].first
  record ? record[:id] : nil
end

def get_verses(ranges, translation_id)
  all = []
  ranges.each do |(ref_from, ref_to)|
    start_id = get_verse_id(ref_from, translation_id)
    stop_id  = get_verse_id(ref_to, translation_id)
    if start_id and stop_id
      all += DB['select * from verses where id between ? and ?', start_id, stop_id].to_a
    else
      return nil
    end
  end
  all
end

get '/' do
  @translations = DB['select identifier, language, name from translations order by language, name']
  @host = (request.env['SCRIPT_URI'] || request.env['REQUEST_URI']).split('?').first
  erb :index
end

get '/:ref' do
  content_type 'application/json; charset=utf-8'
  ref_string = params[:ref].gsub(/\+/, ' ')
  ref = BibleRef::Reference.new(ref_string)
  translation = DB['select * from translations where identifier = ?', params[:translation] || 'WEB'].first
  unless translation
    status 404
    response = { error: 'translation not found' }
    return JSONP(response)
  end
  if ranges = ref.ranges
    if verses = get_verses(ranges, translation[:id])
      verses.map! do |v|
        {
          book_id:   v[:book_id],
          book_name: v[:book],
          chapter:   v[:chapter],
          verse:     v[:verse],
          text:      v[:text]
        }
      end
      response = {
        reference: ref.normalize,
        verses: verses,
        text: verses.map { |v| v[:text] }.join,
        translation_id: translation[:identifier],
        translation_name: translation[:name],
        translation_note: translation[:license]
      }
      JSONP response
    else
      status 404
      response = { error: 'not found' }
      JSONP response
    end
  else
    status 404
    response = { error: 'not found' }
    JSONP response
  end
end
