"""Pydantic schemas for Bible data (akin to C# DTOs / ViewModels)."""
from pydantic import BaseModel
from typing import List, Optional

class Translation(BaseModel):
    identifier: str
    name: str
    language: str
    language_code: str
    license: str

class Verse(BaseModel):
    book_id: str
    book: str
    chapter: int
    verse: int
    text: str

class VerseResponse(BaseModel):
    reference: str
    verses: List[Verse]
    text: str
    translation_id: str
    translation_name: str
    translation_note: str

class BookChapter(BaseModel):
    book_id: str
    book: str
    chapter: int

class ChaptersResponse(BaseModel):
    translation: Translation
    chapters: List[BookChapter]

class VersesInChapterResponse(BaseModel):
    translation: Translation
    verses: List[Verse]

class RandomVerseResponse(BaseModel):
    translation: Translation
    random_verse: Verse
