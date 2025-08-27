require 'spec_helper'

RSpec.describe 'Bible API', type: :request do
  describe 'GET /' do
    context 'without random parameter' do
      it 'returns the HTML index page' do
        get '/'
        expect(last_response).to be_ok
        expect(last_response.content_type).to include('text/html')
      end
    end

    context 'with random parameter (legacy API)' do
      it 'returns a random verse in JSON format' do
        get '/?random=true'
        expect(last_response).to be_ok
        expect(last_response.content_type).to include('application/json')
        expect_cors_headers

        response = json_response
        expect_verse_response_structure(response)
      end

      it 'supports JSONP callback' do
        get '/?random=true&callback=testCallback'
        expect(last_response).to be_ok
        expect(last_response.content_type).to include('text/javascript')
        expect(last_response.body).to start_with('testCallback(')
        expect(last_response.body).to end_with(')')
      end
    end
  end

  describe 'OPTIONS /:ref' do
    it 'returns CORS headers for preflight requests' do
      options '/John+3:16'
      expect(last_response.status).to eq(200)
      expect_cors_headers
    end
  end

  describe 'GET /:ref' do
    context 'with single verse' do
      it 'returns the requested verse' do
        get '/John+3:16'
        expect(last_response).to be_ok
        expect(last_response.content_type).to include('application/json')
        expect_cors_headers

        response = json_response
        expect_verse_response_structure(response)
        expect(response['reference']).to eq('John 3:16')
        expect(response['verses'].length).to eq(1)

        verse = response['verses'].first
        expect(verse['book_id']).to eq('JHN')
        expect(verse['book_name']).to eq('John')
        expect(verse['chapter']).to eq(3)
        expect(verse['verse']).to eq(16)
      end

      it 'supports verse numbers parameter' do
        get '/John+3:16?verse_numbers=true'
        expect(last_response).to be_ok

        response = json_response
        expect(response['text']).to start_with('(16)')
      end

      it 'supports JSONP callback' do
        get '/John+3:16?callback=testCallback'
        expect(last_response).to be_ok
        expect(last_response.content_type).to include('text/javascript')
        expect(last_response.body).to start_with('testCallback(')
      end
    end

    context 'with verse range' do
      it 'returns multiple verses' do
        get '/John+3:16-17'
        expect(last_response).to be_ok

        response = json_response
        expect(response['reference']).to eq('John 3:16-17')
        expect(response['verses']).to be_an(Array)
        expect(response['verses'].length).to eq(2)
        expect(response['verses'][0]['verse']).to eq(16)
        expect(response['verses'][1]['verse']).to eq(17)
      end
    end

    context 'with chapter' do
      it 'returns entire chapter when only chapter specified' do
        get '/John+3'
        expect(last_response).to be_ok

        response = json_response
        expect(response['verses']).not_to be_empty
        expect(response['verses'].all? { |v| v['chapter'] == 3 }).to be true
      end
    end

    context 'with different translation' do
      it 'returns verse from specified translation' do
        get '/John+3:16?translation=kjv'
        expect(last_response).to be_ok

        response = json_response
        expect(response['translation_id']).to eq('kjv')
      end
    end

    context 'with Spanish translations' do
      it 'returns verse from Spanish translation using Spanish book name' do
        get '/Juan+3:16?translation=bes'
        expect(last_response).to be_ok

        response = json_response
        expect(response['translation_id']).to eq('bes')
        expect(response['translation_name']).to eq('La Biblia en Español Sencillo')
        expect(response['verses'][0]['book_name']).to eq('Juan')
        expect(response['verses'][0]['chapter']).to eq(3)
        expect(response['verses'][0]['verse']).to eq(16)
      end

      it 'works with different Spanish translations' do
        get '/G%C3%A9nesis+1:1?translation=rv1909' # URL-encoded Génesis
        expect(last_response).to be_ok

        response = json_response
        expect(response['translation_id']).to eq('rv1909')
        expect(response['translation_name']).to eq('Reina Valera 1909')
        expect(response['verses'][0]['book_name']).to eq('Génesis')
      end

      it 'handles Spanish book names with accents' do
        get '/%C3%89xodo+20:1?translation=bes' # URL-encoded Éxodo
        expect(last_response).to be_ok

        response = json_response
        expect(response['verses'][0]['book_name']).to eq('Éxodo')
        expect(response['verses'][0]['chapter']).to eq(20)
      end

      it 'works with Spanish abbreviations' do
        get '/Mat+5:3?translation=bes'
        expect(last_response).to be_ok

        response = json_response
        expect(response['verses'][0]['book_name']).to eq('Mateo')
        expect(response['verses'][0]['chapter']).to eq(5)
        expect(response['verses'][0]['verse']).to eq(3)
      end
    end

    context 'with single chapter books' do
      it 'handles Jude correctly (single verse)' do
        get '/Jude+1'
        expect(last_response).to be_ok

        response = json_response
        expect(response['verses'].length).to eq(1)
        expect(response['verses'][0]['verse']).to eq(1)
      end

      it 'handles single chapter book matching parameter' do
        get '/Jude+1?single_chapter_book_matching=indifferent'
        expect(last_response).to be_ok

        response = json_response
        # Should return whole chapter when indifferent
        expect(response['verses'].length).to be > 1
      end

      it 'handles single chapter book matching header' do
        header 'X-Single-Chapter-Book-Matching', 'indifferent'
        get '/Jude+1'
        expect(last_response).to be_ok

        response = json_response
        # Should return whole chapter when indifferent
        expect(response['verses'].length).to be > 1
      end

      it 'parameter takes precedence over header' do
        header 'X-Single-Chapter-Book-Matching', 'indifferent'
        get '/Jude+1?single_chapter_book_matching=special'
        expect(last_response).to be_ok

        response = json_response
        # Parameter should override header, so single verse
        expect(response['verses'].length).to eq(1)
        expect(response['verses'][0]['verse']).to eq(1)
      end
    end

    context 'with edge cases' do
      it 'handles spaces in reference' do
        get '/1+John+3:16'
        expect(last_response).to be_ok

        response = json_response
        expect(response['reference']).to eq('1 John 3:16')
      end

      it 'handles book abbreviations' do
        get '/Jn+3:16'
        expect(last_response).to be_ok

        response = json_response
        expect(response['verses'][0]['book_id']).to eq('JHN')
      end

      it 'handles case insensitive references' do
        get '/john+3:16'
        expect(last_response).to be_ok

        response = json_response
        expect(response['verses'][0]['book_id']).to eq('JHN')
      end

      it 'handles references with extra whitespace' do
        get '/John++3:16'
        expect(last_response).to be_ok

        response = json_response
        expect(response['reference']).to eq('John 3:16')
      end
    end

    context 'with invalid references' do
      it 'returns 404 for invalid book' do
        get '/InvalidBook+1:1'
        expect(last_response.status).to eq(404)
        expect(json_response).to include('error' => 'not found')
      end

      it 'returns 404 for invalid chapter' do
        get '/John+999:1'
        expect(last_response.status).to eq(404)
        expect(json_response).to include('error' => 'not found')
      end

      it 'returns 404 for invalid verse' do
        get '/John+3:999'
        expect(last_response.status).to eq(404)
        expect(json_response).to include('error' => 'not found')
      end

      it 'returns 404 for malformed reference' do
        get '/not-a-reference'
        expect(last_response.status).to eq(404)
        expect(json_response).to include('error' => 'not found')
      end
    end

    context 'with special characters' do
      it 'handles URL encoded references' do
        get '/John%203:16'
        expect(last_response).to be_ok

        response = json_response
        expect(response['reference']).to eq('John 3:16')
      end
    end
  end

  describe 'Complex verse references' do
    it 'handles cross-chapter ranges' do
      get '/John+3:16-4:2'
      expect(last_response).to be_ok

      response = json_response
      expect(response['verses']).not_to be_empty
      # Should include verses from both chapters
      chapters = response['verses'].map { |v| v['chapter'] }.uniq
      expect(chapters).to include(3, 4)
    end

    it 'handles multiple chapter references' do
      get '/Psalm+23-24'
      expect(last_response).to be_ok

      response = json_response
      expect(response['verses']).not_to be_empty
      chapters = response['verses'].map { |v| v['chapter'] }.uniq.sort
      expect(chapters).to eq([23, 24])
    end

    it 'handles single verse in multi-chapter book' do
      get '/Genesis+1:1'
      expect(last_response).to be_ok

      response = json_response
      expect(response['verses'].length).to eq(1)
      verse = response['verses'][0]
      expect(verse['book_id']).to eq('GEN')
      expect(verse['chapter']).to eq(1)
      expect(verse['verse']).to eq(1)
    end
  end

  describe 'Book name variations' do
    it 'handles full book names' do
      get '/Revelation+1:1'
      expect(last_response).to be_ok

      response = json_response
      expect(response['verses'][0]['book_id']).to eq('REV')
    end

    it 'handles common abbreviations' do
      get '/Rev+1:1'
      expect(last_response).to be_ok

      response = json_response
      expect(response['verses'][0]['book_id']).to eq('REV')
    end

    it 'handles numbered books' do
      get '/1+Corinthians+13:13'
      expect(last_response).to be_ok

      response = json_response
      expect(response['verses'][0]['book_id']).to eq('1CO')
    end

    it 'handles numbered book abbreviations' do
      get '/1+Cor+13:13'
      expect(last_response).to be_ok

      response = json_response
      expect(response['verses'][0]['book_id']).to eq('1CO')
    end
  end

  describe 'Additional single chapter book tests' do
    %w[Obadiah Philemon 2John 3John].each do |book|
      it "handles #{book} correctly" do
        get "/#{book}+1"
        expect(last_response).to be_ok

        response = json_response
        expect(response['verses']).not_to be_empty
        expect(response['verses'][0]['verse']).to eq(1)
      end
    end

    it 'handles Jude with indifferent matching parameter' do
      get '/Jude+1?single_chapter_book_matching=indifferent'
      expect(last_response).to be_ok

      response = json_response
      # Should return the whole book of Jude
      expect(response['verses'].length).to be > 1
    end

    it 'handles Philemon with indifferent matching header' do
      header 'X-Single-Chapter-Book-Matching', 'indifferent'
      get '/Philemon+1'
      expect(last_response).to be_ok

      response = json_response
      # Should return the whole book of Philemon
      expect(response['verses'].length).to be > 1
    end
  end

  describe 'Psalm reference variations' do
    it 'handles Psalm singular' do
      get '/Psalm+23'
      expect(last_response).to be_ok

      response = json_response
      expect(response['verses'][0]['book_id']).to eq('PSA')
      expect(response['verses'][0]['chapter']).to eq(23)
    end

    it 'handles Psalms plural' do
      get '/Psalms+23'
      expect(last_response).to be_ok

      response = json_response
      expect(response['verses'][0]['book_id']).to eq('PSA')
    end
  end

  describe 'Text formatting and display options' do
    it 'preserves text formatting including newlines' do
      get '/John+3:16'
      expect(last_response).to be_ok

      response = json_response
      # The text should contain the actual verse text
      expect(response['text']).to include('God so loved the world')
      expect(response['verses'][0]['text']).to include('God so loved the world')
    end

    it 'handles verse numbers in text when requested' do
      get '/John+3:16-17?verse_numbers=true'
      expect(last_response).to be_ok

      response = json_response
      expect(response['text']).to include('(16)')
      expect(response['text']).to include('(17)')
    end
  end

  describe 'URL encoding and special characters' do
    it 'handles various encoding formats' do
      # Test different encoding methods for the same reference
      %w[/1+John+3:16 /1%20John%203:16 /1+John%203:16].each do |path|
        get path
        expect(last_response).to be_ok
        response = json_response
        expect(response['verses'][0]['book_id']).to eq('1JN')
      end
    end
  end

  describe 'Large range requests' do
    it 'handles entire single-chapter book requests efficiently' do
      get '/Jude+1' # Get first verse of Jude
      expect(last_response).to be_ok

      response = json_response
      expect(response['verses']).not_to be_empty
      # Should be from Jude
      expect(response['verses'][0]['book_id']).to eq('JUD')
    end

    it 'handles psalm chapter requests' do
      get '/Psalm+1' # Get entire Psalm 1
      expect(last_response).to be_ok

      response = json_response
      expect(response['verses']).not_to be_empty
      chapters = response['verses'].map { |v| v['chapter'] }.uniq.sort
      expect(chapters).to eq([1])
    end
  end

  describe 'Case sensitivity handling' do
    it 'handles different case variations' do
      %w[john JOHN JoHn].each do |book_name|
        get "/#{book_name}+3:16"
        expect(last_response).to be_ok
        response = json_response
        expect(response['verses'][0]['book_id']).to eq('JHN')
      end
    end
  end

  describe 'Boundary condition tests' do
    it 'handles first verse of Bible' do
      get '/Genesis+1:1'
      expect(last_response).to be_ok

      response = json_response
      verse = response['verses'][0]
      expect(verse['book_id']).to eq('GEN')
      expect(verse['chapter']).to eq(1)
      expect(verse['verse']).to eq(1)
    end

    it 'handles last verse of Bible' do
      get '/Revelation+22:21'
      expect(last_response).to be_ok

      response = json_response
      verse = response['verses'][0]
      expect(verse['book_id']).to eq('REV')
      expect(verse['chapter']).to eq(22)
      expect(verse['verse']).to eq(21)
    end

    it 'handles first verse of New Testament' do
      get '/Matthew+1:1'
      expect(last_response).to be_ok

      response = json_response
      verse = response['verses'][0]
      expect(verse['book_id']).to eq('MAT')
      expect(verse['chapter']).to eq(1)
      expect(verse['verse']).to eq(1)
    end
  end

  describe 'Invalid reference handling' do
    it 'returns 404 for verse that is one too high' do
      # Assuming John 3 has 36 verses, test verse 37
      get '/John+3:37'
      expect(last_response.status).to eq(404)
    end

    it 'returns 404 for chapter that is one too high' do
      # Assuming John has 21 chapters, test chapter 22
      get '/John+22:1'
      expect(last_response.status).to eq(404)
    end
  end

  describe 'Content-Type and CORS headers' do
    it 'sets UTF-8 charset for JSON and JSONP responses with CORS headers' do
      get '/John+3:16'
      expect(last_response.content_type).to include('charset=utf-8')
      expect_cors_headers

      get '/John+3:16?callback=test'
      expect(last_response.content_type).to include('charset=utf-8')
    end
  end
end
