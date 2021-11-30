task :deploy do
  sh "rsync -az ./ deploy@bible-api.com:/var/www/apps/bible_api/ && ssh deploy@bible-api.com 'cd /var/www/apps/bible_api && bundle install && touch tmp/restart.txt'"
end
