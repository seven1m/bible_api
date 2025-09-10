# bible\_api (Python Version)

This is a Python web app that serves a JSON API for public domain and open bible translations.

**This is a Python conversion of the original Ruby Bible API project.**

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

### With Python

```python
import requests
import json

response = requests.get('https://bible-api.com/John+3:16')
verse = response.json()
print(json.dumps(verse, indent=2))
```

## Hosting it Yourself

If you want to host this Python application yourself, you'll need a Linux server with Python 3.12+, Redis, and MySQL (or MariaDB) installed. Follow the steps below:

1. Clone the repo:

   ```
   git clone https://github.com/andreidemit/bible_api
   cd bible_api
   git submodule update --init
   ```

2. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Create the database and import the translations:

   ```
   mysql -uroot -e "create database bible_api; grant all on bible_api.* to user@localhost identified by 'password';"
   export DATABASE_URL="mysql://user:password@localhost/bible_api"
   export REDIS_URL="redis://localhost:6379"
   python import_bible.py
   ```

4. Run the application:

   **For development:**
   ```
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   **For production:**
   ```
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

   Or use gunicorn for production:
   ```
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## API Documentation

The Python version includes automatic API documentation:

- **Interactive API docs:** Visit `/docs` when running the server
- **ReDoc documentation:** Visit `/redoc` when running the server

## Key Changes from Ruby Version

- **Framework:** Sinatra → FastAPI
- **ORM:** Sequel → SQLAlchemy
- **Templates:** ERB → Jinja2
- **Rate Limiting:** Rack::Attack → slowapi
- **Language:** Ruby 3.3+ → Python 3.12+
- **Bible Reference Parsing:** Simplified version (Ruby bible_ref gem equivalent)

## Features

- ✅ All original API endpoints preserved
- ✅ CORS support
- ✅ Rate limiting (15 requests per 30 seconds per IP)
- ✅ JSONP support (via callback parameter)
- ✅ Bible reference parsing (John 3:16, Matt 5:1-10, etc.)
- ✅ Multiple translations
- ✅ Random verse API
- ✅ Web interface with API documentation
- ✅ Automatic API documentation (/docs, /redoc)

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest httpx

# Run tests (when implemented)
pytest
```

### Code Formatting

```bash
pip install black isort
black .
isort .
```

## Environment Variables

- `DATABASE_URL`: MySQL database connection string
- `REDIS_URL`: Redis connection string for rate limiting
- `PORT`: Port to run the server on (default: 5000)

## Docker Support

```dockerfile
# Dockerfile example
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Copyright

Copyright [Tim Morgan](https://timmorgan.org). Licensed under The MIT License (MIT). See LICENSE for more info.

**Python conversion:** This conversion maintains the same functionality and API compatibility as the original Ruby version.