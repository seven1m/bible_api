"""Bible API router (versioned)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional, List, Dict, Any
from app.services.providers import get_xml_service
from app.services.azure_xml_service import AzureXMLBibleService
from app.schemas.bible import VerseResponse, RandomVerseResponse, ChaptersResponse, VersesInChapterResponse, Translation as TranslationSchema, Verse as VerseSchema
from app.core.constants import PROTESTANT_BOOKS, OT_BOOKS, NT_BOOKS

router = APIRouter(prefix="/v1", tags=["bible"])

# Helper conversions (temporary; can be centralized later)

def translation_as_dict(translation: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "identifier": translation.get("identifier"),
        "name": translation.get("name"),
        "language": translation.get("language"),
        "language_code": translation.get("language_code"),
        "license": translation.get("license")
    }

def get_translation(azure_service: AzureXMLBibleService, identifier: Optional[str]) -> Dict[str, Any]:
    if not identifier:
        translations = azure_service.list_translations()
        if translations:
            identifier = translations[0]['identifier']
        else:
            raise HTTPException(status_code=500, detail="No translations available")
    translation = azure_service.get_translation_info(identifier.lower())
    if not translation:
        raise HTTPException(status_code=404, detail={"error": "translation not found"})
    return translation

@router.get("/data")
async def list_translations(request: Request, azure_service: AzureXMLBibleService = Depends(get_xml_service)):
    host = str(request.base_url).rstrip('/')
    translations = azure_service.list_translations()
    return {
        "translations": [
            {**translation_as_dict(t), "url": f"{host}/v1/data/{t['identifier']}"}
            for t in translations
        ]
    }

@router.get("/data/{translation_id}")
async def get_translation_books(request: Request, translation_id: str, azure_service: AzureXMLBibleService = Depends(get_xml_service)):
    host = str(request.base_url).rstrip('/')
    translation = get_translation(azure_service, translation_id)
    all_books = azure_service.get_books_for_translation(translation_id)
    books = []
    for book in all_books:
        book_id = book['id'].upper()
        if book_id in PROTESTANT_BOOKS:
            books.append({
                "id": book_id,
                "name": book['name'],
                "url": f"{host}/v1/data/{translation['identifier']}/{book_id}"
            })
    return {"translation": translation_as_dict(translation), "books": books}

@router.get("/data/{translation_id}/random")
async def get_random_verse_endpoint(translation_id: str, azure_service: AzureXMLBibleService = Depends(get_xml_service)):
    translation = get_translation(azure_service, translation_id)
    verse = azure_service.get_random_verse(translation['identifier'], PROTESTANT_BOOKS)
    if not verse:
        raise HTTPException(status_code=404, detail={"error": "error getting verse"})
    return {"translation": translation_as_dict(translation), "random_verse": verse}

@router.get("/data/{translation_id}/random/{book_id}")
async def get_random_verse_by_book(translation_id: str, book_id: str, azure_service: AzureXMLBibleService = Depends(get_xml_service)):
    translation = get_translation(azure_service, translation_id)
    book_id = book_id.upper()
    if book_id == 'OT':
        books = OT_BOOKS
    elif book_id == 'NT':
        books = NT_BOOKS
    else:
        books = book_id.split(',')
    verse = azure_service.get_random_verse(translation['identifier'], books)
    if not verse:
        raise HTTPException(status_code=404, detail={"error": "error getting verse"})
    return {"translation": translation_as_dict(translation), "random_verse": verse}

@router.get("/data/{translation_id}/{book_id}")
async def get_book_chapters(request: Request, translation_id: str, book_id: str, azure_service: AzureXMLBibleService = Depends(get_xml_service)):
    host = str(request.base_url).rstrip('/')
    translation = get_translation(azure_service, translation_id)
    chapters_info = azure_service.get_chapters_for_book(translation_id, book_id)
    if not chapters_info:
        raise HTTPException(status_code=404, detail={"error": "book not found"})
    chapter_list = []
    for chapter_info in chapters_info:
        chapter_list.append({
            "book_id": chapter_info['book_id'],
            "book": chapter_info['book_name'],
            "chapter": chapter_info['chapter'],
            "url": f"{host}/v1/data/{translation['identifier']}/{chapter_info['book_id']}/{chapter_info['chapter']}"
        })
    return {"translation": translation_as_dict(translation), "chapters": chapter_list}

@router.get("/data/{translation_id}/{book_id}/{chapter}")
async def get_chapter_verses(translation_id: str, book_id: str, chapter: int, azure_service: AzureXMLBibleService = Depends(get_xml_service)):
    translation = get_translation(azure_service, translation_id)
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
    return {"translation": translation_as_dict(translation), "verses": verse_list}
