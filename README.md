bible_api
=========

Sinatra web app that serves RESTful JSON web API for the World English Bible.

```
mysql -uroot "create database bible_api; grant all on bible_api.* to user@localhost identified by 'password';"
BIBLE_API_DB="mysql2://user:password@localhost/bible_api" ruby import.rb
BIBLE_API_DB="mysql2://user:password@localhost/bible_api" ruby app.rb
```


http://localhost:4567/John+3:16

```javascript
{
  "reference": "John 3:16",
  "verses": [
    {
      "book_id":   "JHN",
      "book_name": "John",
      "chapter":   3,
      "verse":     16,
      "text":      "\nFor God so loved the world, that he gave his one and only Son, that whoever believes in him should not perish, but have eternal life.\n\n"
    }
  ],
  "text": "\nFor God so loved the world, that he gave his one and only Son, that whoever believes in him should not perish, but have eternal life.\n\n"
}
```

Copyright [Tim Morgan](http://timmorgan.org). See LICENSE.
