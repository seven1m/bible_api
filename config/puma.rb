workers ENV.fetch('WEB_CONCURRENCY') { 2 }
threads_count = ENV.fetch('RAILS_MAX_THREADS') { 3 }
threads threads_count, threads_count

preload_app!

port        ENV.fetch("PORT") { 5000 }
environment ENV.fetch("RACK_ENV") { "development" }
