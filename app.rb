require 'bundler'

Bundler.require
require 'json'
require 'logger'
require 'rack/attack'
require 'redis'
require 'sinatra/reloader'

require 'dotenv'
Dotenv.load

REDIS = Redis.new(url: ENV.fetch('REDIS_URL'))

DB = Sequel.connect(ENV.fetch('DATABASE_URL').sub(%r{mysql://}, 'mysql2://'), encoding: 'utf8mb4', max_connections: 10)
# DB.sql_log_level = :debug
# DB.loggers << Logger.new($stdout)

use Rack::Attack
Rack::Attack.cache.store = Rack::Attack::StoreProxy::RedisStoreProxy.new(REDIS)

RACK_ATTACK_LIMIT = 15
RACK_ATTACK_PERIOD = 30

Rack::Attack.throttle('requests by ip', limit: RACK_ATTACK_LIMIT, period: RACK_ATTACK_PERIOD) { |request| request.ip }

CORS_HEADERS = {
  'Access-Control-Allow-Origin' => '*',
  'Access-Control-Allow-Methods' => %w[OPTIONS GET],
  'Access-Control-Allow-Headers' => ['Content-Type'],
}.freeze

set :protection, except: [:json_csrf]

def get_verse_id(ref, translation_id, last = false)
  record =
    DB[
      'select id from verses ' \
        "where book_id = :book and chapter = :chapter #{ref[:verse] ? 'and verse = :verse' : ''} " \
        'and translation_id = :translation_id ' \
        " #{last ? 'order by id desc' : ''} limit 1",
      ref.update(translation_id: translation_id)
    ].first
  record ? record[:id] : nil
end

def get_verses(ranges, translation_id)
  all = []
  ranges.each do |(ref_from, ref_to)|
    start_id = get_verse_id(ref_from, translation_id)
    stop_id = get_verse_id(ref_to, translation_id, :last)
    return nil unless start_id && stop_id
    all += DB['select * from verses where id between ? and ?', start_id, stop_id].to_a
  end
  all
end

def get_translation(identifier = params[:translation])
  translation = DB['select * from translations where identifier = ?', identifier || 'WEB'].first
  halt 404, jsonp(error: 'translation not found') unless translation
  translation
end

def translation_as_json(translation)
  translation.slice(:identifier, :name, :language, :language_code, :license)
end

def protestant_books
  @protestant_books ||= BibleRef::Canons::Protestant.new.books
end

def ot_books
  @ot_books ||= protestant_books[...protestant_books.index('MAT')]
end

def nt_books
  @nt_books ||= protestant_books[protestant_books.index('MAT')..]
end

def random_verse(translation:, books: protestant_books)
  verse =
    DB[
      'select * from verses where translation_id = :translation_id and book_id in :books order by rand() limit 1',
      { translation_id: translation[:id], books: }
    ].first
  halt 404, jsonp(error: 'error getting verse') if verse.nil?
  verse
end

# pulled from sinatra-jsonp and modified to return a UTF-8 charset
module Sinatra
  module Jsonp
    def jsonp(*args)
      if args.size > 0
        data = MultiJson.dump args[0], pretty: settings.respond_to?(:json_pretty) && settings.json_pretty
        if args.size > 1
          callback = args[1].to_s
        else
          %w[callback jscallback jsonp jsoncallback].each { |x| callback = params.delete(x) unless callback }
        end
        if callback
          callback.tr!('^a-zA-Z0-9_$\.', '')
          content_type 'text/javascript', charset: 'utf-8'
          response = "#{callback}(#{data})"
        else
          content_type 'application/json', charset: 'utf-8'
          response = data
        end
        response
      end
    end
  end
  helpers Jsonp
end

get '/' do
  unless DB.table_exists?(:verses)
    status 500
    return 'please run import.rb script according to README'
  end

  if params[:random]
    # Legacy API we need to keep supporting. Use /data/:translation/random instead.
    headers CORS_HEADERS
    translation = get_translation
    verse = random_verse(translation:)
    ref = "#{verse[:book]} #{verse[:chapter]}:#{verse[:verse]}"
    jsonp(render_response(verses: [verse], ref: ref, translation:))
  else
    @translations = DB['select id, identifier, language, name from translations order by language, name']
    books = DB["select translation_id, book from verses where book_id = 'JHN' group by translation_id, book"]
    @books = books.each_with_object({}) { |book, hash| hash[book[:translation_id]] = book[:book] }
    https = request.env['HTTP_X_FORWARDED_PROTO'] =~ /https/
    @host = request.base_url
    erb :index
  end
end

get '/data' do
  content_type 'application/json', charset: 'utf-8'
  headers CORS_HEADERS

  host = request.base_url
  translations =
    DB['select * from translations order by language, name'].map do |t|
      translation_as_json(t).merge(url: "#{host}/data/#{t.fetch(:identifier)}")
    end
  { translations: }.to_json
end

get '/data/:translation' do
  content_type 'application/json', charset: 'utf-8'
  headers CORS_HEADERS

  host = request.base_url
  translation = get_translation
  books =
    BibleRef::LANGUAGES[translation[:language_code]].new.books.filter_map do |id, config|
      next unless protestant_books.include?(id)
      { id:, name: config[:name], url: "#{host}/data/#{translation.fetch(:identifier)}/#{id}" }
    end

  { translation: translation_as_json(translation), books: }.to_json
end

get '/data/:translation/random' do
  content_type 'application/json', charset: 'utf-8'
  headers CORS_HEADERS

  translation = get_translation
  verse = random_verse(translation:).slice(:book_id, :book, :chapter, :verse, :text)

  { translation: translation_as_json(translation), random_verse: verse }.to_json
end

get '/data/:translation/random/:book_id' do
  content_type 'application/json', charset: 'utf-8'
  headers CORS_HEADERS

  translation = get_translation

  case (book_id = params[:book_id].upcase)
  when 'OT'
    books = ot_books
  when 'NT'
    books = nt_books
  else
    books = book_id.split(',')
    book =
      DB[
        'select distinct book_id from verses where book_id in :books and translation_id = :translation_id',
        books:,
        translation_id: translation[:id]
      ].first
    halt 404, jsonp(error: 'book not found') unless book
  end

  verse = random_verse(translation:, books:).slice(:book_id, :book, :chapter, :verse, :text)

  { translation: translation_as_json(translation), random_verse: verse }.to_json
end

get '/data/:translation/:book_id' do
  content_type 'application/json', charset: 'utf-8'
  headers CORS_HEADERS

  host = request.base_url
  translation = get_translation
  chapters =
    DB[
      'select distinct book_id, book, chapter from verses where book_id = :book_id and translation_id = :translation_id order by chapter',
      book_id: params[:book_id],
      translation_id: translation[:id]
    ].map do |record|
      record.merge(
        url: "#{host}/data/#{translation.fetch(:identifier)}/#{record.fetch(:book_id)}/#{record.fetch(:chapter)}",
      )
    end

  halt 404, jsonp(error: 'book not found') unless chapters.any?

  { translation: translation_as_json(translation), chapters: }.to_json
end

get '/data/:translation/:book_id/:chapter' do
  content_type 'application/json', charset: 'utf-8'
  headers CORS_HEADERS

  translation = get_translation
  verses =
    DB[
      'select book_id, book, chapter, verse, text from verses where book_id = :book_id and chapter = :chapter and translation_id = :translation_id order by chapter, verse',
      book_id: params[:book_id],
      chapter: params[:chapter],
      translation_id: translation[:id]
    ].to_a

  halt 404, jsonp(error: 'book/chapter not found') unless verses.any?

  { translation: translation_as_json(translation), verses: }.to_json
end

options '/:ref' do
  headers CORS_HEADERS
  200
end

get '/:ref' do
  content_type 'application/json', charset: 'utf-8'
  headers CORS_HEADERS
  ref_string = params[:ref].tr('+', ' ')
  display_verse_from(ref_string)
end

def display_verse_from(ref_string)
  translation = get_translation
  # someone DOSing us
  if ref_string =~ /^john.1,2,3,4,5,6,7,8,9,10$/
    status 400
    return 'error'
  end
  ref = BibleRef::Reference.new(ref_string, language: translation[:language_code], single_chapter_book_matching:)
  if (ranges = ref.ranges)
    if (verses = get_verses(ranges, translation[:id]))
      response = render_response(verses: verses, ref: ref.normalize, translation: translation)
    else
      status 404
      response = { error: 'not found' }
    end
  else
    status 404
    response = { error: 'not found' }
  end
  jsonp response
end

def single_chapter_book_matching
  case request.params['single_chapter_book_matching'] || request.env['HTTP_X_SINGLE_CHAPTER_BOOK_MATCHING']
  when 'indifferent'
    # `jude 1` => whole chapter
    :indifferent
  else
    # `jude 1` => single verse
    :special
  end
end

def render_response(verses:, ref:, translation:)
  verses.map! do |v|
    { book_id: v[:book_id], book_name: v[:book], chapter: v[:chapter], verse: v[:verse], text: v[:text] }
  end
  vn = params[:verse_numbers]
  verse_text =
    if vn == 'true'
      verses.map { |v| '(' + v[:verse].to_s + ') ' + v[:text] }.join
    else
      verses.map { |v| v[:text] }.join
    end
  {
    reference: ref,
    verses: verses,
    text: verse_text,
    translation_id: translation[:identifier],
    translation_name: translation[:name],
    translation_note: translation[:license],
  }
end
