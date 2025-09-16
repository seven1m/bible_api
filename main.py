import os
import json
import random
import re
from typing import Optional, Dict, List, Any
from urllib.parse import unquote

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from azure_xml_service import AzureXMLBibleService

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Bible API", description="A JSON API for Bible verses and passages")

# Initialize Azure Bible Service (replaces database)
try:
    print("Initializing Azure Bible Service...")
    azure_service = AzureXMLBibleService()
    print(f"✓ Azure service initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize Azure Bible Service: {e}")
    import traceback
    traceback.print_exc()
    azure_service = None

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Templates
templates = Jinja2Templates(directory="templates")

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
    """Render verse response in the expected format"""
    formatted_verses = []
    for v in verses:
        formatted_verses.append({
            "book_id": v['book_id'],
            "book_name": v['book'],
            "chapter": v['chapter'],
            "verse": v['verse'],
            "text": v['text']
        })
    
    if verse_numbers:
        verse_text = ''.join(f"({v['verse']}) {v['text']}" for v in formatted_verses)
    else:
        verse_text = ''.join(v['text'] for v in formatted_verses)
    
    return {
        "reference": ref,
        "verses": formatted_verses,
        "text": verse_text,
        "translation_id": translation['identifier'],
        "translation_name": translation['name'],
        "translation_note": translation['license']
    }
    
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

# Protestant books list (simplified)
PROTESTANT_BOOKS = [
    'GEN', 'EXO', 'LEV', 'NUM', 'DEU', 'JOS', 'JDG', 'RUT', '1SA', '2SA', '1KI', '2KI',
    '1CH', '2CH', 'EZR', 'NEH', 'EST', 'JOB', 'PSA', 'PRO', 'ECC', 'SNG', 'ISA', 'JER',
    'LAM', 'EZK', 'DAN', 'HOS', 'JOL', 'AMO', 'OBA', 'JON', 'MIC', 'NAM', 'HAB', 'ZEP',
    'HAG', 'ZEC', 'MAL', 'MAT', 'MRK', 'LUK', 'JHN', 'ACT', 'ROM', '1CO', '2CO', 'GAL',
    'EPH', 'PHP', 'COL', '1TH', '2TH', '1TI', '2TI', 'TIT', 'PHM', 'HEB', 'JAS', '1PE',
    '2PE', '1JN', '2JN', '3JN', 'JUD', 'REV'
]

OT_BOOKS = PROTESTANT_BOOKS[:PROTESTANT_BOOKS.index('MAT')]
NT_BOOKS = PROTESTANT_BOOKS[PROTESTANT_BOOKS.index('MAT'):]

# Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, random: Optional[str] = None, translation: Optional[str] = None):
    """Main page - returns API documentation or random verse"""
    
    # Check if Azure service is available
    if not azure_service:
        raise HTTPException(status_code=500, detail="Azure Bible service not available")
    
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
        translations = azure_service.list_translations()
        # Get example books from first translation
        books = {}
        if translations:
            first_trans = translations[0]
            books_list = azure_service.get_books_for_translation(first_trans['identifier'])
            books = {first_trans['identifier']: books_list[0]['name'] if books_list else 'John'}
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "translations": translations,
            "books": books,
            "host": str(request.base_url).rstrip('/')
        })

@app.get("/data")
async def list_translations(request: Request):
    """List all available translations"""
    if not azure_service:
        raise HTTPException(status_code=500, detail="Azure Bible service not available")
    
    host = str(request.base_url).rstrip('/')
    print("DEBUG: Getting translations from Azure service")
    translations = azure_service.list_translations()
    print(f"DEBUG: Found {len(translations)} translations")
    
    result = {
        "translations": [
            {**translation_as_dict(t), "url": f"{host}/data/{t['identifier']}"}
            for t in translations
        ]
    }
    return result

@app.get("/data/{translation_id}")
async def get_translation_books(request: Request, translation_id: str):
    """Get books in a translation"""
    if not azure_service:
        raise HTTPException(status_code=500, detail="Azure Bible service not available")
    
    host = str(request.base_url).rstrip('/')
    translation = get_translation(translation_id)
    
    # Get available books for this translation
    all_books = azure_service.get_books_for_translation(translation_id)
    
    # Filter to Protestant books only
    books = []
    for book in all_books:
        book_id = book['id'].upper()
        if book_id in PROTESTANT_BOOKS:
            books.append({
                "id": book_id,
                "name": book['name'],
                "url": f"{host}/data/{translation['identifier']}/{book_id}"
            })
    
    return {
        "translation": translation_as_dict(translation),
        "books": books
    }

@app.get("/data/{translation_id}/random")
async def get_random_verse_endpoint(request: Request, translation_id: str):
    """Get a random verse from a translation"""
    if not azure_service:
        raise HTTPException(status_code=500, detail="Azure Bible service not available")
    
    translation = get_translation(translation_id)
    verse = get_random_verse(translation, PROTESTANT_BOOKS)
    
    if not verse:
        raise HTTPException(status_code=404, detail={"error": "error getting verse"})
    
    return {
        "translation": translation_as_dict(translation),
        "random_verse": verse
    }

@app.get("/data/{translation_id}/random/{book_id}")
async def get_random_verse_by_book(request: Request, translation_id: str, book_id: str):
    """Get a random verse from specific book(s)"""
    if not azure_service:
        raise HTTPException(status_code=500, detail="Azure Bible service not available")
    
    translation = get_translation(translation_id)
    book_id = book_id.upper()
    
    if book_id == 'OT':
        books = OT_BOOKS
    elif book_id == 'NT':
        books = NT_BOOKS
    else:
        books = book_id.split(',')
        # For Azure service, we'll trust that the books exist and let the service handle it
    
    verse = get_random_verse(translation, books)
    if not verse:
        raise HTTPException(status_code=404, detail={"error": "error getting verse"})
    
    return {
        "translation": translation_as_dict(translation),
        "random_verse": verse
    }

@app.get("/data/{translation_id}/{book_id}")
async def get_book_chapters(request: Request, translation_id: str, book_id: str):
    """Get chapters in a book"""
    if not azure_service:
        raise HTTPException(status_code=500, detail="Azure Bible service not available")
    
    host = str(request.base_url).rstrip('/')
    translation = get_translation(translation_id)
    
    # Get available chapters for this book using the new method
    chapters_info = azure_service.get_chapters_for_book(translation_id, book_id)
    
    if not chapters_info:
        raise HTTPException(status_code=404, detail={"error": "book not found"})
    
    chapter_list = []
    for chapter_info in chapters_info:
        chapter_list.append({
            "book_id": chapter_info['book_id'],
            "book": chapter_info['book_name'],
            "chapter": chapter_info['chapter'],
            "url": f"{host}/data/{translation['identifier']}/{chapter_info['book_id']}/{chapter_info['chapter']}"
        })
    
    return {
        "translation": translation_as_dict(translation),
        "chapters": chapter_list
    }

@app.get("/data/{translation_id}/{book_id}/{chapter}")
async def get_chapter_verses(request: Request, translation_id: str, book_id: str, chapter: int):
    """Get verses in a chapter"""
    if not azure_service:
        raise HTTPException(status_code=500, detail="Azure Bible service not available")
    
    translation = get_translation(translation_id)
    
    verses = azure_service.get_verses_by_reference(translation_id, book_id, chapter)
    
    if not verses:
        raise HTTPException(status_code=404, detail={"error": "book/chapter not found"})
    
    verse_list = []
    for verse in verses:
        verse_list.append({
            "book_id": verse['book_id'],
            "book": verse['book'],
            "chapter": verse['chapter'],
            "verse": verse['verse'],
            "text": verse['text']
        })
    
    return {
        "translation": translation_as_dict(translation),
        "verses": verse_list
    }

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
