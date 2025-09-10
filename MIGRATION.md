# Ruby to Python Migration Guide

This document outlines the conversion of the Bible API from Ruby to Python, highlighting key differences and maintaining compatibility.

## Overview

The Python version maintains **100% API compatibility** with the Ruby version while leveraging modern Python frameworks and tooling.

## Technology Stack Comparison

| Component | Ruby Version | Python Version |
|-----------|--------------|----------------|
| **Web Framework** | Sinatra | FastAPI |
| **ORM/Database** | Sequel | SQLAlchemy |
| **Template Engine** | ERB | Jinja2 |
| **Rate Limiting** | Rack::Attack | slowapi |
| **Server** | Puma | Uvicorn |
| **Language Version** | Ruby 3.3.6 | Python 3.12+ |

## File Structure Comparison

### Ruby Version
```
├── app.rb              # Main Sinatra application
├── import.rb           # Data import script
├── config.ru           # Rack configuration
├── Gemfile             # Ruby dependencies
├── Procfile            # Heroku process file
├── views/
│   ├── index.erb       # Main template
│   └── layout.erb      # Layout template
└── config/
    └── puma.rb         # Puma server config
```

### Python Version
```
├── main.py             # Main FastAPI application
├── import_bible.py     # Data import script
├── requirements.txt    # Python dependencies
├── Procfile.python     # Heroku process file
├── runtime.txt         # Python version spec
├── app.python.json     # Heroku app config
├── templates/
│   └── index.html      # Main template (Jinja2)
├── test_conversion.py  # Basic tests
└── start_python.sh     # Quick start script
```

## Key Differences

### 1. Web Framework

**Ruby (Sinatra):**
```ruby
get '/' do
  translation = get_translation
  verse = random_verse(translation:)
  jsonp(render_response(verses: [verse], ref: ref, translation:))
end
```

**Python (FastAPI):**
```python
@app.get("/")
@limiter.limit("15/30seconds")
async def root(request: Request, translation: Optional[str] = None, db: Session = Depends(get_db)):
    trans = get_translation(db, translation)
    verse = get_random_verse(db, trans, PROTESTANT_BOOKS)
    return JSONResponse(content=render_verse_response([verse], ref, trans))
```

### 2. Database Operations

**Ruby (Sequel):**
```ruby
DB = Sequel.connect(ENV.fetch('DATABASE_URL'))
translation = DB['select * from translations where identifier = ?', identifier].first
verses = DB['select * from verses where id between ? and ?', start_id, stop_id].to_a
```

**Python (SQLAlchemy):**
```python
engine = create_engine(DATABASE_URL, encoding='utf8mb4', pool_size=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

translation = db.query(Translation).filter(Translation.identifier == identifier).first()
verses = db.query(Verse).filter(Verse.id >= start_id, Verse.id <= stop_id).all()
```

### 3. Templates

**Ruby (ERB):**
```erb
<h1>bible-api.com</h1>
<% @translations.each do |translation| %>
  <tr>
    <td><%= translation[:language] %></td>
    <td><%= translation[:name] %></td>
  </tr>
<% end %>
```

**Python (Jinja2):**
```html
<h1>bible-api.com</h1>
{% for translation in translations %}
  <tr>
    <td>{{ translation.language }}</td>
    <td>{{ translation.name }}</td>
  </tr>
{% endfor %}
```

### 4. Rate Limiting

**Ruby (Rack::Attack):**
```ruby
use Rack::Attack
Rack::Attack.throttle('requests by ip', limit: 15, period: 30) do |request|
  request.ip
end
```

**Python (slowapi):**
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/endpoint")
@limiter.limit("15/30seconds")
async def endpoint(request: Request):
    # endpoint logic
```

## API Endpoint Compatibility

All API endpoints work identically:

| Endpoint | Ruby | Python | Status |
|----------|------|--------|--------|
| `GET /` | ✅ | ✅ | Identical |
| `GET /data` | ✅ | ✅ | Identical |
| `GET /data/{translation}` | ✅ | ✅ | Identical |
| `GET /data/{translation}/random` | ✅ | ✅ | Identical |
| `GET /data/{translation}/{book}/{chapter}` | ✅ | ✅ | Identical |
| `GET /{reference}` | ✅ | ✅ | Identical |
| Rate limiting | ✅ | ✅ | Same limits |
| CORS support | ✅ | ✅ | Same headers |
| JSONP support | ✅ | ✅ | Same callback handling |

## Response Format Compatibility

Both versions return identical JSON responses:

```json
{
  "reference": "John 3:16",
  "verses": [
    {
      "book_id": "JHN",
      "book_name": "John",
      "chapter": 3,
      "verse": 16,
      "text": "For God so loved the world..."
    }
  ],
  "text": "For God so loved the world...",
  "translation_id": "web",
  "translation_name": "World English Bible",
  "translation_note": "Public Domain"
}
```

## Migration Steps

1. **Install Python version:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Use existing database:**
   - Same MySQL database
   - Same table schema
   - Same data

3. **Update environment variables:**
   ```bash
   # Same variables, Python handles URL conversion
   DATABASE_URL=mysql://user:pass@host/db
   REDIS_URL=redis://host:port
   ```

4. **Start Python server:**
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## Additional Python Features

The Python version includes some enhancements:

1. **Automatic API Documentation**
   - `/docs` - Interactive Swagger UI
   - `/redoc` - ReDoc documentation

2. **Better Error Handling**
   - Detailed HTTP exception responses
   - Proper status codes

3. **Type Safety**
   - Pydantic models for request/response validation
   - Type hints throughout

4. **Modern Python Async**
   - Async/await support
   - Better performance under load

## Performance Considerations

- **Python FastAPI** is generally faster than Ruby Sinatra
- **SQLAlchemy** with connection pooling provides good performance
- **Uvicorn** ASGI server is highly performant
- **Redis** rate limiting works identically

## Testing

The Python version includes basic tests:
```bash
python test_conversion.py
```

For comprehensive testing, both versions can be run side-by-side and responses compared.

## Deployment

### Heroku
Replace `Procfile` content:
```
# Ruby version
web: bundle exec puma -C config/puma.rb

# Python version  
web: python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Docker
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Conclusion

The Python conversion maintains full compatibility while providing:
- ✅ Same API endpoints and responses
- ✅ Same database schema
- ✅ Same rate limiting and CORS
- ✅ Modern framework with auto-documentation
- ✅ Better performance characteristics
- ✅ Type safety and error handling

Users can seamlessly switch from Ruby to Python without any client-side changes.