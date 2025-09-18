# Bible API (Python Port)

This repository is a Python (FastAPI) port and adaptation of the original Ruby-based Bible API project. It serves a JSON API for public domain Bible translations. Data is read directly from XML files stored in Azure Blob Storage (no relational database required).

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

## Running Locally

### Prerequisites
* Python 3.12+
* (Optional) Docker / Docker Compose
* An Azure Blob Storage account containing supported public domain translation XML files.

### Environment Variables (Core)
| Variable | Purpose | Default |
|----------|---------|---------|
| `AZURE_STORAGE_CONNECTION_STRING` | Connection string to the storage account | (required) |
| `AZURE_CONTAINER_NAME` | Blob container with translation XML files | `bible-translations` |
| `PORT` | HTTP port | `8000` |

Create a `.env` file:
```
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=...<your-connection-string>...
AZURE_CONTAINER_NAME=bible-translations
PORT=8000
```

### Run (Plain Python)
```
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Run with Docker Compose (Dev Hot Reload)
```
docker compose up dev --build
```

### Production-like Container
```
docker compose up api --build -d
```

Visit `http://localhost:8000` then `http://localhost:8000/docs` for interactive API documentation.

## Testing

An initial pytest-based test suite is being introduced.

Install development dependencies (includes application + test packages):

```
pip install -r requirements-dev.txt
```

Run the tests:

```
pytest -q
```

Generate a coverage report:

```
pytest --cov=app --cov=main --cov-report=term-missing
```

The test suite uses a lightweight in-memory fake service instead of connecting to Azure. For integration tests against a real storage account, set the usual environment variables and (optionally) mark such tests with `-m azure` once those are added.

Existing legacy scripts (`test_conversion.py`, `test_azure_endpoints.py`) will be migrated or deprecated in favor of structured pytest modules.

## API Documentation

The Python version includes automatic API documentation:

- **Interactive API docs:** Visit `/docs` when running the server
- **ReDoc documentation:** Visit `/redoc` when running the server

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

## Test Coverage & Next Steps

Current pytest suite (see `tests/`):
- Unit: reference parsing, response rendering, translation selection fallback.
- API: `/v1/data` family, random verse endpoints, chapter & verse retrieval, dynamic reference endpoint, HTML root.
- Deterministic fake service ensures tests run without Azure credentials.

Planned / potential additions:
- Integration tests hitting a real Azure Blob container (guarded by marker `azure` & env vars).
- Stress/performance sampling for large XML translations.
- Additional parsing robustness tests for more complex reference syntaxes.

Suggested coverage target: 80%+ for helper/service modules (excluding Azure SDK branches). Run `pytest --cov=app --cov=main --cov-report=term-missing` for a line summary.

## Architecture Changes vs Original Ruby Version

| Aspect | Original (Ruby) | Python Port |
|--------|-----------------|-------------|
| Language | Ruby (Sinatra) | Python (FastAPI) |
| Storage | SQL + import pipeline | Direct Azure Blob XML parsing (cached in memory) |
| Rate limiting | Redis-based | (Not implemented yet in this port) |
| Docs | Manual | Auto (Swagger/OpenAPI) |
| Random verses | DB query | In-memory random selection from parsed verses |

If rate limiting or additional caching are needed later, a lightweight Redis integration or an API gateway (e.g. Azure API Management) can be added.

## Licensing

Source Code:
- MIT License. See `LICENSE`.
- Original Ruby implementation © 2014 Tim Morgan (retained per MIT requirements).
- Python port and adaptations © 2025 Andrei Demit.

Bible Translation Data:
- All translations used with this project (in Blob Storage) are public domain.
- If a future non–public-domain translation is added, it must be listed in `NOTICE` (and possibly a `DATA_LICENSES.md`).

See `NOTICE` for a concise attribution summary.

---
Contributions and improvements are welcome. Open issues or pull requests for feature requests, bug fixes, or new public domain translations.
