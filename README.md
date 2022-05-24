# bible\_api

This is a Ruby web app that serves a JSON API for public domain and open bible translations.

## Using It

This app is served from [bible-api.com](https://bible-api.com/), which anyone can use.

### With Curl and JQ

```sh
→ curl -s https://bible-api.com/John+3:16 | jq
{
  "reference": "John 3:16",
  "verses": [
    {
      "book_id": "JHN",
      "book_name": "John",
      "chapter": 3,
      "verse": 16,
      "text": "\nFor God so loved the world, that he gave his one and only Son, that whoever believes in him should not perish, but have eternal life.\n\n"
    }
  ],
  "text": "\nFor God so loved the world, that he gave his one and only Son, that whoever believes in him should not perish, but have eternal life.\n\n",
  "translation_id": "web",
  "translation_name": "World English Bible",
  "translation_note": "Public Domain"
}
```

### With Ruby

```sh
→ ruby -r open-uri -r json -r pp -e "pp JSON.parse(URI.open('https://bible-api.com/John+3:16').read)"
{"reference"=>"John 3:16",
 "verses"=>
  [{"book_id"=>"JHN",
    "book_name"=>"John",
    "chapter"=>3,
    "verse"=>16,
    "text"=>
     "\n" +
     "For God so loved the world, that he gave his one and only Son, that whoever believes in him should not perish, but have eternal life.\n" +
     "\n"}],
 "text"=>
  "\n" +
  "For God so loved the world, that he gave his one and only Son, that whoever believes in him should not perish, but have eternal life.\n" +
  "\n",
 "translation_id"=>"web",
 "translation_name"=>"World English Bible",
 "translation_note"=>"Public Domain"}
```

## Hosting it Yourself

If you want to host this application yourself, you'll need a Linux server with Ruby and MySQL (or MariaDB) installed. Follow the steps below:

1. Clone the repo:

   ```
   git clone https://github.com/seven1m/bible_api
   cd bible_api
   git submodule update --init
   ```

2. Install the dependencies:

   ```
   gem install bundler
   bundle config --local deployment true # optional, but prefered on a server
   bundle install
   ```

3. Create the database and import the translations:

   ```
   mysql -uroot -e "create database bible_api; grant all on bible_api.* to user@localhost identified by 'password';"
   export DATABASE_URL="mysql2://user:password@localhost/bible_api"
   bundle exec ruby import.rb
   ```

4. Host the app with [Passenger](https://www.phusionpassenger.com/docs/advanced_guides/install_and_upgrade/standalone/install/)

   ... or run `bundle exec ruby app.rb` if you are just testing.

## Copyright

Copyright [Tim Morgan](https://timmorgan.org). Licensed under The MIT License (MIT). See LICENSE for more info.
