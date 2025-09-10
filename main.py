import os
import json
import random
import re
from typing import Optional, Dict, List, Any
from urllib.parse import unquote

from fastapi import FastAPI, Request, HTTPException, Query, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, select, func, and_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Bible API", description="A JSON API for Bible verses and passages")

# Redis for rate limiting
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
limiter = Limiter(key_func=get_remote_address, storage_uri=os.getenv('REDIS_URL', 'redis://localhost:6379'))
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', '')
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('mysql://', 'mysql+pymysql://')
    # Add charset to URL instead of using deprecated encoding parameter
    if 'charset' not in DATABASE_URL:
        connector = '&' if '?' in DATABASE_URL else '?'
        DATABASE_URL += f'{connector}charset=utf8mb4'
    engine = create_engine(DATABASE_URL, pool_size=10)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # For testing without database
    engine = None
    SessionLocal = None

Base = declarative_base()

# Database models
class Translation(Base):
    __tablename__ = 'translations'
    
    id = Column(Integer, primary_key=True)
    identifier = Column(String(255))
    name = Column(String(255))
    language = Column(String(255))
    language_code = Column(String(255))
    license = Column(String(255))

class Verse(Base):
    __tablename__ = 'verses'
    
    id = Column(Integer, primary_key=True)
    book_num = Column(Integer)
    book_id = Column(String(255))
    book = Column(String(255))
    chapter = Column(Integer)
    verse = Column(Integer)
    text = Column(Text)
    translation_id = Column(Integer)

# Templates
templates = Jinja2Templates(directory="templates")

# Rate limiting constants
RACK_ATTACK_LIMIT = 15
RACK_ATTACK_PERIOD = 30

# Helper functions
def get_db():
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_translation(db: Session, identifier: str = None) -> Translation:
    """Get translation by identifier, defaulting to WEB"""
    if not identifier:
        identifier = 'web'
    
    translation = db.query(Translation).filter(Translation.identifier == identifier.lower()).first()
    if not translation:
        raise HTTPException(status_code=404, detail={"error": "translation not found"})
    return translation

def translation_as_dict(translation: Translation) -> Dict[str, Any]:
    """Convert translation object to dictionary"""
    return {
        "identifier": translation.identifier,
        "name": translation.name,
        "language": translation.language,
        "language_code": translation.language_code,
        "license": translation.license
    }

def get_verse_id(db: Session, ref: Dict[str, Any], translation_id: int, last: bool = False) -> Optional[int]:
    """Get verse ID by reference"""
    query = db.query(Verse.id).filter(
        Verse.book_id == ref['book'],
        Verse.chapter == ref['chapter'],
        Verse.translation_id == translation_id
    )
    
    if 'verse' in ref and ref['verse']:
        query = query.filter(Verse.verse == ref['verse'])
    
    if last:
        query = query.order_by(Verse.id.desc())
    
    result = query.first()
    return result[0] if result else None

def get_verses(db: Session, ranges: List[tuple], translation_id: int) -> Optional[List[Dict]]:
    """Get verses by ranges"""
    all_verses = []
    for ref_from, ref_to in ranges:
        start_id = get_verse_id(db, ref_from, translation_id)
        stop_id = get_verse_id(db, ref_to, translation_id, last=True)
        
        if not start_id or not stop_id:
            return None
            
        verses = db.query(Verse).filter(
            Verse.id >= start_id,
            Verse.id <= stop_id
        ).all()
        
        for verse in verses:
            all_verses.append({
                'id': verse.id,
                'book_id': verse.book_id,
                'book': verse.book,
                'chapter': verse.chapter,
                'verse': verse.verse,
                'text': verse.text,
                'translation_id': verse.translation_id
            })
    
    return all_verses

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

def render_verse_response(verses: List[Dict], ref: str, translation: Translation, verse_numbers: bool = False) -> Dict[str, Any]:
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
        "translation_id": translation.identifier,
        "translation_name": translation.name,
        "translation_note": translation.license
    }

def get_random_verse(db: Session, translation: Translation, books: Optional[List[str]] = None) -> Optional[Dict]:
    """Get a random verse"""
    query = db.query(Verse).filter(Verse.translation_id == translation.id)
    
    if books:
        query = query.filter(Verse.book_id.in_(books))
    
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
@limiter.limit(f"{RACK_ATTACK_LIMIT}/{RACK_ATTACK_PERIOD}seconds")
async def root(request: Request, random: Optional[str] = None, translation: Optional[str] = None, db: Session = Depends(get_db)):
    """Main page - returns API documentation or random verse"""
    
    # Check if database tables exist
    if not engine.dialect.has_table(engine.connect(), 'verses'):
        raise HTTPException(status_code=500, detail="Please run import script according to README")
    
    if random is not None:
        # Legacy random API support
        trans = get_translation(db, translation)
        verse = get_random_verse(db, trans, PROTESTANT_BOOKS)
        if not verse:
            raise HTTPException(status_code=404, detail={"error": "error getting verse"})
        
        ref = f"{verse['book']} {verse['chapter']}:{verse['verse']}"
        response = render_verse_response([verse], ref, trans)
        return JSONResponse(content=response)
    else:
        # Return HTML documentation page
        translations = db.query(Translation).order_by(Translation.language, Translation.name).all()
        books_query = db.query(Verse.translation_id, Verse.book).filter(Verse.book_id == 'JHN').group_by(Verse.translation_id, Verse.book).all()
        books = {book.translation_id: book.book for book in books_query}
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "translations": translations,
            "books": books,
            "host": str(request.base_url).rstrip('/'),
            "RACK_ATTACK_LIMIT": RACK_ATTACK_LIMIT,
            "RACK_ATTACK_PERIOD": RACK_ATTACK_PERIOD
        })

@app.get("/data")
@limiter.limit(f"{RACK_ATTACK_LIMIT}/{RACK_ATTACK_PERIOD}seconds")
async def list_translations(request: Request, db: Session = Depends(get_db)):
    """List all available translations"""
    host = str(request.base_url).rstrip('/')
    translations = db.query(Translation).order_by(Translation.language, Translation.name).all()
    
    result = {
        "translations": [
            {**translation_as_dict(t), "url": f"{host}/data/{t.identifier}"}
            for t in translations
        ]
    }
    return result

@app.get("/data/{translation_id}")
@limiter.limit(f"{RACK_ATTACK_LIMIT}/{RACK_ATTACK_PERIOD}seconds")
async def get_translation_books(request: Request, translation_id: str, db: Session = Depends(get_db)):
    """Get books in a translation"""
    host = str(request.base_url).rstrip('/')
    translation = get_translation(db, translation_id)
    
    # Get available books for this translation
    book_ids = db.query(Verse.book_id, Verse.book).filter(
        Verse.translation_id == translation.id,
        Verse.book_id.in_(PROTESTANT_BOOKS)
    ).distinct().all()
    
    books = []
    for book_id, book_name in book_ids:
        books.append({
            "id": book_id,
            "name": book_name,
            "url": f"{host}/data/{translation.identifier}/{book_id}"
        })
    
    return {
        "translation": translation_as_dict(translation),
        "books": books
    }

@app.get("/data/{translation_id}/random")
@limiter.limit(f"{RACK_ATTACK_LIMIT}/{RACK_ATTACK_PERIOD}seconds")
async def get_random_verse_endpoint(request: Request, translation_id: str, db: Session = Depends(get_db)):
    """Get a random verse from a translation"""
    translation = get_translation(db, translation_id)
    verse = get_random_verse(db, translation, PROTESTANT_BOOKS)
    
    if not verse:
        raise HTTPException(status_code=404, detail={"error": "error getting verse"})
    
    return {
        "translation": translation_as_dict(translation),
        "random_verse": verse
    }

@app.get("/data/{translation_id}/random/{book_id}")
@limiter.limit(f"{RACK_ATTACK_LIMIT}/{RACK_ATTACK_PERIOD}seconds")
async def get_random_verse_by_book(request: Request, translation_id: str, book_id: str, db: Session = Depends(get_db)):
    """Get a random verse from specific book(s)"""
    translation = get_translation(db, translation_id)
    book_id = book_id.upper()
    
    if book_id == 'OT':
        books = OT_BOOKS
    elif book_id == 'NT':
        books = NT_BOOKS
    else:
        books = book_id.split(',')
        # Verify books exist for this translation
        existing_book = db.query(Verse).filter(
            Verse.book_id.in_(books),
            Verse.translation_id == translation.id
        ).first()
        if not existing_book:
            raise HTTPException(status_code=404, detail={"error": "book not found"})
    
    verse = get_random_verse(db, translation, books)
    if not verse:
        raise HTTPException(status_code=404, detail={"error": "error getting verse"})
    
    return {
        "translation": translation_as_dict(translation),
        "random_verse": verse
    }

@app.get("/data/{translation_id}/{book_id}")
@limiter.limit(f"{RACK_ATTACK_LIMIT}/{RACK_ATTACK_PERIOD}seconds")
async def get_book_chapters(request: Request, translation_id: str, book_id: str, db: Session = Depends(get_db)):
    """Get chapters in a book"""
    host = str(request.base_url).rstrip('/')
    translation = get_translation(db, translation_id)
    
    chapters = db.query(Verse.book_id, Verse.book, Verse.chapter).filter(
        Verse.book_id == book_id.upper(),
        Verse.translation_id == translation.id
    ).distinct().order_by(Verse.chapter).all()
    
    if not chapters:
        raise HTTPException(status_code=404, detail={"error": "book not found"})
    
    chapter_list = []
    for chapter in chapters:
        chapter_list.append({
            "book_id": chapter.book_id,
            "book": chapter.book,
            "chapter": chapter.chapter,
            "url": f"{host}/data/{translation.identifier}/{chapter.book_id}/{chapter.chapter}"
        })
    
    return {
        "translation": translation_as_dict(translation),
        "chapters": chapter_list
    }

@app.get("/data/{translation_id}/{book_id}/{chapter}")
@limiter.limit(f"{RACK_ATTACK_LIMIT}/{RACK_ATTACK_PERIOD}seconds")
async def get_chapter_verses(request: Request, translation_id: str, book_id: str, chapter: int, db: Session = Depends(get_db)):
    """Get verses in a chapter"""
    translation = get_translation(db, translation_id)
    
    verses = db.query(Verse).filter(
        Verse.book_id == book_id.upper(),
        Verse.chapter == chapter,
        Verse.translation_id == translation.id
    ).order_by(Verse.chapter, Verse.verse).all()
    
    if not verses:
        raise HTTPException(status_code=404, detail={"error": "book/chapter not found"})
    
    verse_list = []
    for verse in verses:
        verse_list.append({
            "book_id": verse.book_id,
            "book": verse.book,
            "chapter": verse.chapter,
            "verse": verse.verse,
            "text": verse.text
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
@limiter.limit(f"{RACK_ATTACK_LIMIT}/{RACK_ATTACK_PERIOD}seconds")
async def get_verse_by_reference(
    request: Request,
    ref: str, 
    translation: Optional[str] = None,
    verse_numbers: Optional[str] = None,
    single_chapter_book_matching: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get verse(s) by Bible reference"""
    ref_string = unquote(ref).replace('+', ' ')
    
    trans = get_translation(db, translation)
    ranges = parse_bible_reference(ref_string)
    
    if not ranges:
        raise HTTPException(status_code=404, detail={"error": "not found"})
    
    verses = get_verses(db, ranges, trans.id)
    if not verses:
        raise HTTPException(status_code=404, detail={"error": "not found"})
    
    verse_nums = verse_numbers == 'true'
    response = render_verse_response(verses, ref_string, trans, verse_nums)
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))