require 'spec_helper'

RSpec.describe 'Data API Endpoints', type: :request do
  describe 'GET /data' do
    it 'returns list of all translations' do
      get '/data'
      expect(last_response).to be_ok
      expect(last_response.content_type).to include('application/json')
      expect_cors_headers

      response = json_response
      expect(response).to have_key('translations')
      expect(response['translations']).to be_an(Array)
      expect(response['translations']).not_to be_empty

      translation = response['translations'].first
      expect_translation_structure(translation)
      expect(translation).to have_key('url')
      expect(translation['url']).to match(%r{/data/[^/]+$})
    end

    it 'includes expected translations' do
      get '/data'
      response = json_response

      identifiers = response['translations'].map { |t| t['identifier'] }
      expect(identifiers).to include('web') # World English Bible should be available
    end

    it 'orders translations by language and name' do
      get '/data'
      response = json_response

      # Check that translations are ordered (at least not in random order)
      languages = response['translations'].map { |t| t['language'] }
      expect(languages).to eq(languages.sort)
    end

    it 'returns the exact expected list of translations' do
      get '/data'
      response = json_response

      expected_translations = {
        'cherokee' => {
          name: 'Cherokee New Testament',
          language: 'Cherokee',
        },
        'cuv' => {
          name: 'Chinese Union Version',
          language: 'Chinese',
        },
        'bkr' => {
          name: 'Bible kralická',
          language: 'Czech',
        },
        'asv' => {
          name: 'American Standard Version (1901)',
          language: 'English',
        },
        'bbe' => {
          name: 'Bible in Basic English',
          language: 'English',
        },
        'darby' => {
          name: 'Darby Bible',
          language: 'English',
        },
        'dra' => {
          name: 'Douay-Rheims 1899 American Edition',
          language: 'English',
        },
        'kjv' => {
          name: 'King James Version',
          language: 'English',
        },
        'web' => {
          name: 'World English Bible',
          language: 'English',
        },
        'ylt' => {
          name: 'Young\'s Literal Translation (NT only)',
          language: 'English',
        },
        'oeb-cw' => {
          name: 'Open English Bible, Commonwealth Edition',
          language: 'English (UK)',
        },
        'webbe' => {
          name: 'World English Bible, British Edition',
          language: 'English (UK)',
        },
        'oeb-us' => {
          name: 'Open English Bible, US Edition',
          language: 'English (US)',
        },
        'clementine' => {
          name: 'Clementine Latin Vulgate',
          language: 'Latin',
        },
        'almeida' => {
          name: 'João Ferreira de Almeida',
          language: 'Portuguese',
        },
        'rccv' => {
          name: 'Protestant Romanian Corrected Cornilescu Version',
          language: 'Romanian',
        },
        'synodal' => {
          name: 'Russian Synodal Translation',
          language: 'Russian',
        },
      }

      expect(response['translations'].length).to eq(expected_translations.length)

      response['translations'].each do |translation|
        identifier = translation['identifier']
        expect(expected_translations).to have_key(identifier), "Unexpected translation: #{identifier}"

        expected = expected_translations[identifier]
        expect(translation['name']).to eq(expected[:name])
        expect(translation['language']).to eq(expected[:language])
      end
    end
  end

  describe 'Translation book lists stability' do
    let(:expected_protestant_book_ids) do
      %w[
        GEN
        EXO
        LEV
        NUM
        DEU
        JOS
        JDG
        RUT
        1SA
        2SA
        1KI
        2KI
        1CH
        2CH
        EZR
        NEH
        EST
        JOB
        PSA
        PRO
        ECC
        SNG
        ISA
        JER
        LAM
        EZK
        DAN
        HOS
        JOL
        AMO
        OBA
        JON
        MIC
        NAM
        HAB
        ZEP
        HAG
        ZEC
        MAL
        MAT
        MRK
        LUK
        JHN
        ACT
        ROM
        1CO
        2CO
        GAL
        EPH
        PHP
        COL
        1TH
        2TH
        1TI
        2TI
        TIT
        PHM
        HEB
        JAS
        1PE
        2PE
        1JN
        2JN
        3JN
        JUD
        REV
      ]
    end

    let(:expected_nt_book_ids) do
      %w[MAT MRK LUK JHN ACT ROM 1CO 2CO GAL EPH PHP COL 1TH 2TH 1TI 2TI TIT PHM HEB JAS 1PE 2PE 1JN 2JN 3JN JUD REV]
    end

    let(:english_book_names) do
      {
        'GEN' => 'Genesis',
        'EXO' => 'Exodus',
        'LEV' => 'Leviticus',
        'NUM' => 'Numbers',
        'DEU' => 'Deuteronomy',
        'JOS' => 'Joshua',
        'JDG' => 'Judges',
        'RUT' => 'Ruth',
        '1SA' => '1 Samuel',
        '2SA' => '2 Samuel',
        '1KI' => '1 Kings',
        '2KI' => '2 Kings',
        '1CH' => '1 Chronicles',
        '2CH' => '2 Chronicles',
        'EZR' => 'Ezra',
        'NEH' => 'Nehemiah',
        'EST' => 'Esther',
        'JOB' => 'Job',
        'PSA' => 'Psalms',
        'PRO' => 'Proverbs',
        'ECC' => 'Ecclesiastes',
        'SNG' => 'Song of Solomon',
        'ISA' => 'Isaiah',
        'JER' => 'Jeremiah',
        'LAM' => 'Lamentations',
        'EZK' => 'Ezekiel',
        'DAN' => 'Daniel',
        'HOS' => 'Hosea',
        'JOL' => 'Joel',
        'AMO' => 'Amos',
        'OBA' => 'Obadiah',
        'JON' => 'Jonah',
        'MIC' => 'Micah',
        'NAM' => 'Nahum',
        'HAB' => 'Habakkuk',
        'ZEP' => 'Zephaniah',
        'HAG' => 'Haggai',
        'ZEC' => 'Zechariah',
        'MAL' => 'Malachi',
        'MAT' => 'Matthew',
        'MRK' => 'Mark',
        'LUK' => 'Luke',
        'JHN' => 'John',
        'ACT' => 'Acts',
        'ROM' => 'Romans',
        '1CO' => '1 Corinthians',
        '2CO' => '2 Corinthians',
        'GAL' => 'Galatians',
        'EPH' => 'Ephesians',
        'PHP' => 'Philippians',
        'COL' => 'Colossians',
        '1TH' => '1 Thessalonians',
        '2TH' => '2 Thessalonians',
        '1TI' => '1 Timothy',
        '2TI' => '2 Timothy',
        'TIT' => 'Titus',
        'PHM' => 'Philemon',
        'HEB' => 'Hebrews',
        'JAS' => 'James',
        '1PE' => '1 Peter',
        '2PE' => '2 Peter',
        '1JN' => '1 John',
        '2JN' => '2 John',
        '3JN' => '3 John',
        'JUD' => 'Jude',
        'REV' => 'Revelation',
      }
    end

    # Test full Bible translations (66 books)
    %w[web kjv asv bbe darby dra webbe oeb-cw oeb-us clementine almeida rccv synodal bkr ylt cuv].each do |translation|
      it "returns exactly 66 Protestant books for #{translation} translation" do
        get "/data/#{translation}"
        expect(last_response).to be_ok

        response = json_response
        expect(response['books'].length).to eq(66),
        "Expected 66 books for #{translation}, got #{response['books'].length}"

        # Verify book IDs match expected Protestant canon
        actual_book_ids = response['books'].map { |b| b['id'] }
        expect(actual_book_ids).to eq(expected_protestant_book_ids),
        "Book IDs don't match Protestant canon for #{translation}"

        # Verify each book has required fields
        response['books'].each do |book|
          expect(book).to include('id', 'name', 'url')
          expect(book['name']).to be_a(String)
          expect(book['name']).not_to be_empty
        end
      end
    end

    # Test English translations have English book names
    %w[web kjv asv bbe darby dra webbe oeb-cw oeb-us].each do |translation|
      it "returns English book names for #{translation} translation" do
        get "/data/#{translation}"
        response = json_response

        response['books'].each do |book|
          expect(book['name']).to eq(english_book_names[book['id']]),
          "Wrong English name for #{book['id']} in #{translation}: expected '#{english_book_names[book['id']]}', got '#{book['name']}'"
        end
      end
    end

    # Test NT-only translation (Cherokee)
    it 'returns exactly 27 New Testament books for cherokee translation' do
      get '/data/cherokee'
      expect(last_response).to be_ok

      response = json_response
      expect(response['books'].length).to eq(27)

      # Verify book IDs match NT canon
      actual_book_ids = response['books'].map { |b| b['id'] }
      expect(actual_book_ids).to eq(expected_nt_book_ids)

      # Verify each book has required fields and Cherokee names
      response['books'].each do |book|
        expect(book).to include('id', 'name', 'url')
        expect(book['name']).to be_a(String)
        expect(book['name']).not_to be_empty
        # Cherokee names should contain Cherokee characters
        expect(book['name']).to match(/[\u13A0-\u13F5]/)
      end
    end

    # Test non-English translations have localized names
    {
      'almeida' => /[áâãçêôõ]/, # Portuguese characters
      'rccv' => /[ăâîșț]/, # Romanian characters
      'synodal' => /[а-я]/, # Cyrillic characters
      'cuv' => /[\u4e00-\u9fff]/, # Chinese characters
    }.each do |translation, pattern|
      it "returns localized book names for #{translation} translation" do
        get "/data/#{translation}"
        response = json_response

        # At least some books should have localized characters
        localized_books = response['books'].select { |book| book['name'].match?(pattern) }
        expect(localized_books).not_to be_empty,
        "Expected some books in #{translation} to have localized names matching #{pattern}"
      end
    end

    it 'verifies book order is consistent (Genesis to Revelation for full Bibles)' do
      get '/data/web'
      response = json_response

      book_ids = response['books'].map { |b| b['id'] }
      expect(book_ids).to eq(expected_protestant_book_ids), 'Books are not in canonical order'
    end

    it 'verifies all book URLs follow correct pattern' do
      get '/data/web'
      response = json_response

      response['books'].each do |book|
        expect(book['url']).to match(%r{/data/web/#{book['id']}$}),
        "Invalid URL pattern for book #{book['id']}: #{book['url']}"
      end
    end

    it 'verifies translation metadata consistency' do
      %w[web kjv cherokee cuv almeida].each do |translation|
        get "/data/#{translation}"
        expect(last_response).to be_ok

        response = json_response
        expect(response).to have_key('translation')
        expect(response).to have_key('books')

        expect_translation_structure(response['translation'])
        expect(response['translation']['identifier']).to eq(translation)
      end
    end
  end

  describe 'GET /data/:translation' do
    it 'returns translation info and books for valid translation' do
      get '/data/web'
      expect(last_response).to be_ok
      expect(last_response.content_type).to include('application/json')
      expect_cors_headers

      response = json_response
      expect(response).to have_key('translation')
      expect(response).to have_key('books')

      expect_translation_structure(response['translation'])
      expect(response['translation']['identifier']).to eq('web')

      expect(response['books']).to be_an(Array)
      expect(response['books']).not_to be_empty

      book = response['books'].first
      expect(book).to include('id' => be_a(String), 'name' => be_a(String), 'url' => be_a(String))
    end

    it 'includes all 66 Protestant books' do
      get '/data/web'
      response = json_response

      expect(response['books'].length).to eq(66)

      # Check for some key books
      book_ids = response['books'].map { |b| b['id'] }
      expect(book_ids).to include('GEN', 'EXO', 'PSA', 'ISA', 'MAT', 'JHN', 'ROM', 'REV')
    end

    it 'provides proper URLs for each book' do
      get '/data/web'
      response = json_response

      book = response['books'].first
      expect(book['url']).to match(%r{/data/web/[A-Z0-9]+$})
    end

    it 'includes book names' do
      get '/data/web'
      response = json_response

      genesis = response['books'].find { |b| b['id'] == 'GEN' }
      expect(genesis['name']).to eq('Genesis')

      john = response['books'].find { |b| b['id'] == 'JHN' }
      expect(john['name']).to eq('John')
    end

    it 'returns 404 for invalid translation' do
      get '/data/invalid_translation'
      expect(last_response.status).to eq(404)
      expect(json_response).to include('error' => 'translation not found')
    end
  end

  describe 'GET /data/:translation/random' do
    it 'returns random verse for valid translation' do
      get '/data/web/random'
      expect(last_response).to be_ok
      expect(last_response.content_type).to include('application/json')
      expect_cors_headers

      response = json_response
      expect(response).to have_key('translation')
      expect(response).to have_key('random_verse')

      expect_translation_structure(response['translation'])
      expect(response['translation']['identifier']).to eq('web')

      verse = response['random_verse']
      expect(verse).to include(
        'book_id' => be_a(String),
        'book' => be_a(String),
        'chapter' => be_a(Integer),
        'verse' => be_a(Integer),
        'text' => be_a(String),
      )
    end

    it 'returns different verses on multiple calls' do
      verses = []
      5.times do
        get '/data/web/random'
        response = json_response
        verse_ref =
          "#{response['random_verse']['book_id']} #{response['random_verse']['chapter']}:#{response['random_verse']['verse']}"
        verses << verse_ref
      end

      # Should have some variety (not all the same verse)
      expect(verses.uniq.length).to be > 1
    end

    it 'returns 404 for invalid translation' do
      get '/data/invalid/random'
      expect(last_response.status).to eq(404)
      expect(json_response).to include('error' => 'translation not found')
    end
  end

  describe 'GET /data/:translation/random/:book_id' do
    context 'with specific book' do
      it 'returns random verse from specified book' do
        get '/data/web/random/JHN'
        expect(last_response).to be_ok
        expect(last_response.content_type).to include('application/json')
        expect_cors_headers

        response = json_response
        expect(response).to have_key('translation')
        expect(response).to have_key('random_verse')

        expect(response['translation']['identifier']).to eq('web')
        expect(response['random_verse']['book_id']).to eq('JHN')
      end
    end

    context 'with Old Testament' do
      it 'returns random verse from OT' do
        get '/data/web/random/OT'
        expect(last_response).to be_ok

        response = json_response
        ot_books = %w[
          GEN
          EXO
          LEV
          NUM
          DEU
          JOS
          JDG
          RUT
          1SA
          2SA
          1KI
          2KI
          1CH
          2CH
          EZR
          NEH
          EST
          JOB
          PSA
          PRO
          ECC
          SNG
          ISA
          JER
          LAM
          EZK
          DAN
          HOS
          JOL
          AMO
          OBA
          JON
          MIC
          NAM
          HAB
          ZEP
          HAG
          ZEC
          MAL
        ]
        expect(ot_books).to include(response['random_verse']['book_id'])
      end
    end

    context 'with New Testament' do
      it 'returns random verse from NT' do
        get '/data/web/random/NT'
        expect(last_response).to be_ok

        response = json_response
        nt_books = %w[
          MAT
          MRK
          LUK
          JHN
          ACT
          ROM
          1CO
          2CO
          GAL
          EPH
          PHP
          COL
          1TH
          2TH
          1TI
          2TI
          TIT
          PHM
          HEB
          JAS
          1PE
          2PE
          1JN
          2JN
          3JN
          JUD
          REV
        ]
        expect(nt_books).to include(response['random_verse']['book_id'])
      end
    end

    context 'with multiple books' do
      it 'returns random verse from specified books' do
        get '/data/web/random/JHN,MAT'
        expect(last_response).to be_ok

        response = json_response
        expect(%w[JHN MAT]).to include(response['random_verse']['book_id'])
      end
    end

    it 'returns 404 for invalid book' do
      get '/data/web/random/INVALID'
      expect(last_response.status).to eq(404)
      expect(json_response).to include('error' => 'book not found')
    end
  end

  describe 'GET /data/:translation/:book_id' do
    it 'returns chapters for valid book' do
      get '/data/web/JHN'
      expect(last_response).to be_ok
      expect(last_response.content_type).to include('application/json')
      expect_cors_headers

      response = json_response
      expect(response).to have_key('translation')
      expect(response).to have_key('chapters')

      expect(response['translation']['identifier']).to eq('web')
      expect(response['chapters']).to be_an(Array)
      expect(response['chapters']).not_to be_empty

      chapter = response['chapters'].first
      expect(chapter).to include(
        'book_id' => 'JHN',
        'book' => be_a(String),
        'chapter' => be_a(Integer),
        'url' => be_a(String),
      )
    end

    it 'returns 404 for invalid book' do
      get '/data/web/INVALID'
      expect(last_response.status).to eq(404)
      expect(json_response).to include('error' => 'book not found')
    end
  end

  describe 'GET /data/:translation/:book_id/:chapter' do
    it 'returns verses for valid book and chapter' do
      get '/data/web/JHN/3'
      expect(last_response).to be_ok
      expect(last_response.content_type).to include('application/json')
      expect_cors_headers

      response = json_response
      expect(response).to have_key('translation')
      expect(response).to have_key('verses')

      expect(response['translation']['identifier']).to eq('web')
      expect(response['verses']).to be_an(Array)
      expect(response['verses']).not_to be_empty

      verse = response['verses'].first
      expect(verse).to include(
        'book_id' => 'JHN',
        'book' => be_a(String),
        'chapter' => 3,
        'verse' => be_a(Integer),
        'text' => be_a(String),
      )
    end

    it 'returns 404 for invalid book/chapter combination' do
      get '/data/web/JHN/999'
      expect(last_response.status).to eq(404)
      expect(json_response).to include('error' => 'book/chapter not found')
    end
  end

  describe 'Content negotiation and headers' do
    it 'returns JSON with UTF-8 charset and CORS headers' do
      get '/data'
      expect(last_response.content_type).to include('application/json')
      expect(last_response.content_type).to include('charset=utf-8')
      expect_cors_headers
    end
  end
end
