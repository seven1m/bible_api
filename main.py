import os
import json
import random
import re
from typing import Optional, Dict, List, Any
from urllib.parse import unquote

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.services.azure_xml_service import AzureXMLBibleService
from app.schemas.bible import Verse as VerseSchema, VerseResponse as VerseResponseSchema
from app.routers.bible import router as bible_router
from app.core.constants import PROTESTANT_BOOKS, OT_BOOKS, NT_BOOKS

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Bible API", description="A JSON API for Bible verses and passages")

# Mount static assets (favicon, future css/js)
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

azure_service = None  # Will lazy init on first need

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Templates
templates = Jinja2Templates(directory="templates")

# Favicon & health endpoints
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Return bible icon as favicon. Served from static directory if present."""
    svg_path = os.path.join("static", "favicon.svg")
    # Some browsers prefer an ICO mime; we return SVG with proper type (modern browsers support it)
    if os.path.exists(svg_path):
        return FileResponse(svg_path, media_type="image/svg+xml")
    # Fallback: empty 204 so we stop 404 noise
    return Response(status_code=204)

@app.get("/healthz", include_in_schema=False)
async def healthz():
    return {"status": "ok"}

# Helper functions
def get_translation(identifier: Optional[str] = None) -> Dict[str, Any]:
    """Get translation by identifier, defaulting to first available"""
    if not azure_service:
        raise HTTPException(status_code=500, detail="Azure service not available")
    
    if not identifier:
        # Get first available translation
        translations = azure_service.list_translations()
        if translations:
            identifier = translations[0]['identifier']
        else:
            raise HTTPException(status_code=500, detail="No translations available")
    
    translation = azure_service.get_translation_info(identifier.lower())
    if not translation:
        raise HTTPException(status_code=404, detail={"error": "translation not found"})
    return translation

def translation_as_dict(translation: Dict[str, Any]) -> Dict[str, Any]:
    """Convert translation object to dictionary (compatibility function)"""
    return {
        "identifier": translation.get("identifier"),
        "name": translation.get("name"),
        "language": translation.get("language"),
        "language_code": translation.get("language_code"),
        "license": translation.get("license")
    }

def get_verses(ranges: List[tuple], translation_id: str) -> Optional[List[Dict]]:
    """Get verses by ranges using Azure service"""
    if not azure_service:
        return None
    
    all_verses = []
    for ref_from, ref_to in ranges:
        # Extract range information
        book = ref_from['book']
        chapter = ref_from['chapter']
        verse_start = ref_from.get('verse')
        verse_end = ref_to.get('verse') if ref_to['chapter'] == chapter else None
        
        verses = azure_service.get_verses_by_reference(
            translation_id, book, chapter, verse_start, verse_end
        )
        all_verses.extend(verses)
    
    return all_verses if all_verses else None

def get_random_verse(translation: Dict[str, Any], books: Optional[List[str]] = None) -> Optional[Dict]:
    """Get a random verse using Azure service"""
    if not azure_service:
        return None
    
def parse_bible_reference(ref_string: str) -> Optional[List[tuple]]:
    """Simple Bible reference parser (simplified version)"""
    # This is a simplified parser. In production, we'd want a more robust solution
    # like porting the bible_ref Ruby gem functionality
    
    # Clean the reference
    ref_string = ref_string.strip().replace('+', ' ')
    
    # Simple pattern matching for basic references like "John 3:16" or "Matt 5:1-10"
    book_chapter_verse_pattern = r'^(\d?\s*[A-Za-z]+)\s+(\d+):(\d+)(?:-(\d+))?(?:,(\d+)(?:-(\d+))?)*$'
    match = re.match(book_chapter_verse_pattern, ref_string)
    
    if not match:
        return None
    
    # Map common book names (simplified)
    book_map = {
        'john': 'JHN', 'jn': 'JHN', 'joh': 'JHN',
        'matt': 'MAT', 'matthew': 'MAT', 'mat': 'MAT', 'mt': 'MAT',
        'mark': 'MRK', 'mk': 'MRK', 'mar': 'MRK',
        'luke': 'LUK', 'lk': 'LUK', 'luk': 'LUK',
        'genesis': 'GEN', 'gen': 'GEN', 'ge': 'GEN',
        'exodus': 'EXO', 'exo': 'EXO', 'ex': 'EXO',
        'psalm': 'PSA', 'psalms': 'PSA', 'ps': 'PSA', 'psa': 'PSA'
    }
    
    book_name = match.group(1).lower().strip()
    book_id = book_map.get(book_name, book_name.upper()[:3])
    chapter = int(match.group(2))
    verse_start = int(match.group(3))
    verse_end = int(match.group(4)) if match.group(4) else verse_start
    
    # Create reference dictionaries
    ref_from = {'book': book_id, 'chapter': chapter, 'verse': verse_start}
    ref_to = {'book': book_id, 'chapter': chapter, 'verse': verse_end}
    
    return [(ref_from, ref_to)]

def render_verse_response(verses: List[Dict], ref: str, translation: Dict[str, Any], verse_numbers: bool = False) -> Dict[str, Any]:
    """Render verse response in the expected format using Pydantic schemas (still returns dict for backward compatibility)."""
    verse_models: List[VerseSchema] = []
    for v in verses:
        verse_models.append(VerseSchema(
            book_id=v['book_id'],
            book=v['book'],
            chapter=v['chapter'],
            verse=v['verse'],
            text=v['text']
        ))

    if verse_numbers:
        verse_text = ''.join(f"({vm.verse}) {vm.text}" for vm in verse_models)
    else:
        verse_text = ''.join(vm.text for vm in verse_models)

    resp = VerseResponseSchema(
        reference=ref,
        verses=verse_models,
        text=verse_text,
        translation_id=translation['identifier'],
        translation_name=translation['name'],
        translation_note=translation['license']
    )
    # Return dict so existing clients unaffected (FastAPI can serialize model directly later if desired)
    return resp.model_dump()
    
    # Use ORDER BY RAND() equivalent
    verse = query.order_by(func.rand()).first()
    
    if not verse:
        return None
        
    return {
        'book_id': verse.book_id,
        'book': verse.book,
        'chapter': verse.chapter,
        'verse': verse.verse,
        'text': verse.text
    }

def _ensure_service():
    global azure_service
    if azure_service is None:
        try:
            print("Lazy-initializing Azure Bible Service...")
            azure_service = AzureXMLBibleService()
            print("✓ Azure service ready")
        except Exception as e:
            print(f"✗ Failed to initialize Azure Bible Service: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="Azure Bible service not available")
    return azure_service

# Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, random: Optional[str] = None, translation: Optional[str] = None):
    """Main page - returns API documentation or random verse"""
    
    # Check if Azure service is available
    service = _ensure_service()
    
    if random is not None:
        # Legacy random API support
        trans = get_translation(translation)
        verse = get_random_verse(trans, PROTESTANT_BOOKS)
        if not verse:
            raise HTTPException(status_code=404, detail={"error": "error getting verse"})
        
        ref = f"{verse['book']} {verse['chapter']}:{verse['verse']}"
        response = render_verse_response([verse], ref, trans)
        return JSONResponse(content=response)
    else:
        # Return HTML documentation page
        translations = service.list_translations()
        # Build example book mapping for each translation (first available book or fallback to 'John')
        example_books = {}
        for t in translations:
            try:
                blist = service.get_books_for_translation(t['identifier'])
                example_books[t['identifier']] = (blist[0]['name'] if blist else 'John')
            except Exception:
                example_books[t['identifier']] = 'John'

        api_base = f"{str(request.base_url).rstrip('/')}/v1"
        return templates.TemplateResponse("index.html", {
            "request": request,
            "translations": translations,
            "example_books": example_books,
            "host": str(request.base_url).rstrip('/'),
            "api_base": api_base
        })

app.include_router(bible_router)

@app.options("/{ref:path}")
async def options_handler():
    """Handle OPTIONS requests for CORS"""
    return {}

@app.get("/{ref:path}")
async def get_verse_by_reference(
    request: Request,
    ref: str, 
    translation: Optional[str] = None,
    verse_numbers: Optional[str] = None,
    single_chapter_book_matching: Optional[str] = None
):
    """Get verse(s) by Bible reference"""
    if not azure_service:
        raise HTTPException(status_code=500, detail="Azure Bible service not available")
    
    ref_string = unquote(ref).replace('+', ' ')
    
    trans = get_translation(translation)
    ranges = parse_bible_reference(ref_string)
    
    if not ranges:
        raise HTTPException(status_code=404, detail={"error": "not found"})
    
    verses = get_verses(ranges, trans['identifier'])
    if not verses:
        raise HTTPException(status_code=404, detail={"error": "not found"})
    
    verse_nums = verse_numbers == 'true'
    response = render_verse_response(verses, ref_string, trans, verse_nums)
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
