require 'bundler/setup'
require 'sinatra'
require "sinatra/jsonp"
require './app'

root_dir = File.dirname(__FILE__)

set :environment, (ENV['RACK_ENV'] || 'production').to_sym

set :root, root_dir
set :app_file, File.join(root_dir, 'app.rb')
disable :run

FileUtils.mkdir_p 'log' unless File.exist?('log')
log = File.new("#{root_dir}/log/sinatra.log", "a")
$stderr.reopen(log)

run Sinatra::Application
