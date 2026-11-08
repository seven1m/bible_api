require 'spec_helper'
require 'tempfile'
require_relative '../../lib/bible_importer'

RSpec.describe BibleImporter do
  let(:importer) { described_class.new(DB, output: StringIO.new) }
  let(:translation) do
    {
      identifier: "import-spec-#{Process.pid}",
      name: 'Import test',
      language: 'English',
      language_code: 'eng',
      license: 'Public Domain',
    }
  end

  around { |example| DB.transaction(rollback: :always, auto_savepoint: true) { example.run } }

  def with_source(xml)
    Tempfile.create(%w[bible-import .xml]) do |file|
      file.write(xml)
      file.flush
      yield file.path
    end
  end

  it 'keeps Traditional and Simplified Chinese as separate translations' do
    translations = described_class.translations(File.expand_path('../../bibles', __dir__))
    expect(translations.map { |item| item[:identifier] }.uniq.size).to eq(translations.size)
    expect(translations.find { |item| item[:identifier] == 'cuv' }[:language_code]).to eq('zh-tw')
    expect(translations.find { |item| item[:identifier] == 'cuv-simp' }[:language_code]).to eq('zh-cn')
    expect(translations.find { |item| item[:identifier] == 'bes' }[:license]).to include(
      'https://creativecommons.org/licenses/by/4.0',
    )
  end

  it 'imports untitled OSIS books using localized book names' do
    xml =
      '<osis><osisText><div type="book" osisID="Gen"><chapter osisID="Gen.1"><verse osisID="Gen.1.1">First.</verse></chapter></div></osisText></osis>'
    with_source(xml) do |path|
      expect(importer.import(path, translation)).to eq(1)
      id = DB[:translations].where(identifier: translation[:identifier]).get(:id)
      expect(DB[:verses].where(translation_id: id).first).to include(
        book_id: 'GEN',
        book: 'Genesis',
        chapter: 1,
        verse: 1,
        text: 'First.',
      )
    end
  end

  it 'normalizes the Hebrew source book IDs' do
    xml = '<usfx><book id="JOE"><h>יואל</h><c id="1"/><v id="1"/>First.<ve/></book></usfx>'
    with_source(xml) do |path|
      rows = importer.each_verse(path, translation.merge(language_code: 'heb')).to_a
      expect(rows.first).to include(book_id: 'JOL', book: 'יואל')
    end
  end

  it 'trims surrounding whitespace while preserving spacing inside a verse' do
    xml = '<usfx><book id="GEN"><h>Genesis</h><c id="1"/><v id="1"/> &#160;First.  Second.&#160; <ve/></book></usfx>'
    with_source(xml) { |path| expect(importer.each_verse(path, translation).first[:text]).to eq('First.  Second.') }
  end

  it 'preserves the previous import if replacement fails' do
    id = DB[:translations].insert(translation)
    DB[:verses].insert(translation_id: id, book_id: 'GEN', chapter: 1, verse: 1, text: 'Original.')
    xml = '<usfx><book id="GEN"><h>Genesis</h><c id="1"/><v id="1"/>First.<ve/><v id="1"/>Duplicate.<ve/></book></usfx>'
    with_source(xml) do |path|
      expect { importer.import(path, translation, overwrite: true) }.to raise_error(/Duplicate reference/)
    end
    expect(DB[:translations].where(identifier: translation[:identifier]).get(:id)).to eq(id)
    expect(DB[:verses].where(translation_id: id).select_map(:text)).to eq(['Original.'])
  end

  it 'joins lettered verse parts and orders the chapter for range lookups' do
    xml =
      '<osis><osisText><div type="book" osisID="Exod"><chapter osisID="Exod.22"><verse osisID="Exod.22.3!b">Second.</verse><verse osisID="Exod.22.2">Other.</verse><verse osisID="Exod.22.3!a">First.</verse></chapter></div></osisText></osis>'
    with_source(xml) do |path|
      rows = importer.each_verse(path, translation).to_a
      expect(rows.map { |row| row[:verse] }).to eq([2, 3])
      expect(rows.last[:text]).to eq('First.Second.')
    end
  end
end
