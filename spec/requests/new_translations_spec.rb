require 'spec_helper'

RSpec.describe 'New translations', type: :request do
  {
    'cuv-simp' => '约翰福音',
    'danish' => 'Johannes',
    'statenvertaling' => 'Johannes',
    'biblia' => 'Joh',
    'luther1912' => 'Johannes',
    'karoli' => 'János',
    'riveduta' => 'Giovanni',
    'kougo' => 'ヨハネによる福音書',
    'bungo' => 'ヨハネによる福音書',
    'korean' => '요한복음',
    'norwegian' => 'Johannes',
    'gdanska' => 'Jana',
    'synodal' => 'Иоанна',
    'swahili' => 'Yohana',
    'swedish' => 'Johannes',
    'tagalog' => 'Juan',
    'cadman' => 'Giăng',
  }.each do |translation, book|
    it "serves #{translation} using a localized reference" do
      get "/#{ERB::Util.url_encode("#{book} 3:16")}", translation: translation
      expect(last_response).to be_ok
      expect(json_response['verses'].first).to include('book_id' => 'JHN', 'chapter' => 3, 'verse' => 16)
      expect(json_response['text'].strip).not_to be_empty
    end
  end

  it 'serves Hebrew Genesis and advertises it on the homepage' do
    get "/#{ERB::Util.url_encode('בראשית 3:16')}", translation: 'leningrad'
    expect(last_response).to be_ok
    expect(json_response['verses'].first['book_id']).to eq('GEN')
    get '/'
    expect(last_response).to be_ok
    expect(last_response.body).to include('translation=leningrad')
  end

  it 'returns the complete Japanese verse after joining its lettered parts' do
    get '/data/kougo/EXO/22'
    expect(last_response).to be_ok
    verses = json_response['verses']
    expect(verses.map { |verse| verse['verse'] }).to eq((1..31).to_a)
    expect(verses.find { |verse| verse['verse'] == 3 }['text']).to include('しかし', '必ず')
  end

  it 'serves trimmed Hungarian text and separates adjacent verses' do
    get "/#{ERB::Util.url_encode('János 3:16-17')}", translation: 'karoli'
    expect(last_response).to be_ok
    texts = json_response['verses'].map { |verse| verse['text'] }
    expect(texts).to all(match(/\A\S(?:.*\S)?\z/m))
    expect(json_response['text']).to eq(texts.join(' '))
  end
end
