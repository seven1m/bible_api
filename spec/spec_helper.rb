require 'rack/test'
require 'rspec'
require 'json'

# Set test environment
ENV['RACK_ENV'] = 'test'

# Load the app
require_relative '../app'

RSpec.configure do |config|
  config.include Rack::Test::Methods

  # Disable Rack::Attack for tests
  config.before(:suite) { Rack::Attack.enabled = false }

  config.expect_with :rspec do |expectations|
    expectations.include_chain_clauses_in_custom_matcher_descriptions = true
  end

  config.mock_with :rspec do |mocks|
    mocks.verify_partial_doubles = true
  end

  config.shared_context_metadata_behavior = :apply_to_host_groups
  config.filter_run_when_matching :focus
  config.disable_monkey_patching!
  config.warnings = true

  # Don't show slow examples
  config.profile_examples = false

  config.order = :random
  Kernel.srand config.seed
end

def app
  Sinatra::Application
end

# Helper method to parse JSON responses
def json_response
  JSON.parse(last_response.body)
end

# Helper method to check CORS headers
def expect_cors_headers
  expect(last_response.headers['Access-Control-Allow-Origin']).to eq('*')
  expect(last_response.headers['Access-Control-Allow-Methods']).to include('GET')
  expect(last_response.headers['Access-Control-Allow-Headers']).to include('Content-Type')
end

# Helper methods for JSON structure validation
def expect_verse_structure(verse)
  expect(verse).to include(
    'book_id' => be_a(String),
    'book_name' => be_a(String),
    'chapter' => be_a(Integer),
    'verse' => be_a(Integer),
    'text' => be_a(String),
  )
end

def expect_translation_structure(translation)
  expect(translation).to include(
    'identifier' => be_a(String),
    'name' => be_a(String),
    'language' => be_a(String),
    'language_code' => be_a(String),
    'license' => be_a(String),
  )
end

def expect_verse_response_structure(response)
  expect(response).to include(
    'reference' => be_a(String),
    'verses' => be_an(Array),
    'text' => be_a(String),
    'translation_id' => be_a(String),
    'translation_name' => be_a(String),
    'translation_note' => be_a(String),
  )
  expect(response['verses']).not_to be_empty
  expect_verse_structure(response['verses'].first)
end
