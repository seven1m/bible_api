"""Local file XML integration test (offline).

This test loads a tiny OSIS sample (``sample-mini.osis.xml``) to exercise the real
FastAPI route stack without hitting Azure or parsing a large file.

Approach:
 - Provide a minimal service implementing only the methods the routes under test call.
 - Override dependency only inside this test (no impact on rest of suite / production).
 - Keep dataset deterministic and very small for speed.
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from fastapi.testclient import TestClient
import main as main_module
from app.services.providers import get_xml_service as real_get_xml_service
import pytest

TRANSLATION_ID = 'sample-mini'
OSIS_PATH = os.path.join(os.path.dirname(__file__), 'sample-mini.osis.xml')


class LocalFileXMLBibleService:
    """Lightweight reader for a single tiny OSIS file (fast).

    Provides just enough of the AzureXMLBibleService interface for the routes invoked here.
    The mini OSIS contains:
      - Genesis 1:1-3
      - John 3:16
    Deterministic responses keep this test stable and very quick (<5ms parse time).
    """
    def __init__(self, path: str, identifier: str):
        self.path = path
        self.identifier = identifier
        with open(self.path, 'r', encoding='utf-8') as f:
            xml = f.read()
        self._root = ET.fromstring(xml)
        self._books_index = None
        self._verses_cache = {}

    # Interface methods used by routes
    def list_translations(self):
        return [{
            'identifier': self.identifier,
            'name': 'Local KJV (OSIS)',
            'language': 'english',
            'language_code': 'en',
            'license': 'Public Domain',
            'file_path': self.path
        }]

    def get_translation_info(self, identifier: str):
        return self.list_translations()[0] if identifier.lower() == self.identifier else None

    def get_books_for_translation(self, translation_id: str):
        # Build once: collect book IDs from osisID or div tags
        if self._books_index is None:
            root = self._root  # type: ignore[assignment]
            books = []
            # OSIS books are often inside div type="book" with osisID
            for div in root.findall('.//{http://www.bibletechnologies.net/2003/OSIS/namespace}div'):
                if div.get('type') == 'book':
                    osis_id = div.get('osisID') or ''
                    if osis_id:
                        norm = osis_id.split('.')[0]
                        books.append({'id': norm[:3].upper(), 'name': norm})
            self._books_index = books
        return self._books_index

    def get_chapters_for_book(self, translation_id: str, book: str):
        root = self._root  # type: ignore[assignment]
        chapters = []
        prefix = f"{book.title()}."
        seen = set()
        for elem in root.iter():
            osis_id = elem.get('osisID')
            if osis_id and osis_id.startswith(prefix):
                parts = osis_id.split('.')
                if len(parts) >= 2:
                    try:
                        ch = int(parts[1])
                        if ch not in seen:
                            seen.add(ch)
                            chapters.append({'book_id': book.upper(), 'book_name': book.title(), 'chapter': ch})
                    except ValueError:
                        continue
        return sorted(chapters, key=lambda x: x['chapter'])

    def get_verses_by_reference(self, translation_id: str, book: str, chapter: int, verse_start=None, verse_end=None):
        root = self._root  # type: ignore[assignment]
        key = (book.upper(), chapter)
        if key not in self._verses_cache:
            verses = []
            chapter_prefix = f"{book.title()}.{chapter}."
            for elem in root.iter():
                osis_id = elem.get('osisID')
                if osis_id and osis_id.startswith(chapter_prefix):
                    parts = osis_id.split('.')
                    if len(parts) >= 3:
                        try:
                            vnum = int(parts[2])
                        except ValueError:
                            continue
                        text = ''.join(elem.itertext()).strip()
                        if text:
                            verses.append({'id': len(verses)+1,'book_id': book.upper(),'book': book.title(),'chapter': chapter,'verse': vnum,'text': text,'translation_id': self.identifier})
            self._verses_cache[key] = sorted(verses, key=lambda x: x['verse'])
        verses = self._verses_cache[key]
        if verse_start is None and verse_end is None:
            return verses
        return [v for v in verses if (verse_start or 0) <= v['verse'] <= (verse_end or 10**6)]

    def get_random_verse(self, translation_id: str, books=None):
        # Deterministic: first verse of first book
        all_books = [b['id'] for b in self.get_books_for_translation(translation_id)]
        if not all_books:
            return None
        first_book = all_books[0]
        chs = self.get_chapters_for_book(translation_id, first_book)
        if not chs:
            return None
        verses = self.get_verses_by_reference(translation_id, first_book, chs[0]['chapter'])
        return verses[0] if verses else None


@pytest.fixture()
def local_service():
    return LocalFileXMLBibleService(OSIS_PATH, TRANSLATION_ID)


def test_local_translation_listing_and_access(local_service):
    # Override dependencies just for this test
    previous_override = main_module.app.dependency_overrides.get(real_get_xml_service)
    previous_global = getattr(main_module, 'azure_service', None)
    main_module.app.dependency_overrides[real_get_xml_service] = lambda: local_service
    main_module.azure_service = local_service  # root-level reference endpoints rely on this
    try:
        client = TestClient(main_module.app)
        r = client.get('/v1/data')
        assert r.status_code == 200
        ids = {t['identifier'] for t in r.json()['translations']}
        assert TRANSLATION_ID in ids

        # Examine book list
        r_books = client.get(f'/v1/data/{TRANSLATION_ID}')
        assert r_books.status_code == 200
        books_payload = r_books.json()
        book_ids = {b['id'] for b in books_payload['books']}
        # Mini file must have exactly GEN and JOH
        assert book_ids == {'GEN', 'JOH'}
        # Chapters for Genesis
        r_ch = client.get(f'/v1/data/{TRANSLATION_ID}/GEN')
        assert r_ch.status_code == 200
        chapters = r_ch.json().get('chapters', [])
        assert chapters == [{'book_id': 'GEN', 'book_name': 'Gen', 'chapter': 1}]

        # Verses for Genesis 1
        r_vs = client.get(f'/v1/data/{TRANSLATION_ID}/GEN/1')
        assert r_vs.status_code == 200
        verses = r_vs.json().get('verses', [])
        verse_numbers = [v['verse'] for v in verses]
        assert verse_numbers == [1, 2, 3]

        # Verses for John 3 (ensure John 3:16 is present and text non-empty)
        r_john = client.get(f'/v1/data/{TRANSLATION_ID}/JOH/3')
        assert r_john.status_code == 200
        john_verses = r_john.json().get('verses', [])
        assert any(v['verse'] == 16 for v in john_verses), 'John 3:16 missing in mini OSIS'
        j316 = next(v for v in john_verses if v['verse'] == 16)
        assert j316['text'].strip(), 'John 3:16 text unexpectedly empty'
    finally:
        # Cleanup override
        if previous_override is not None:
            main_module.app.dependency_overrides[real_get_xml_service] = previous_override
        else:
            main_module.app.dependency_overrides.pop(real_get_xml_service, None)
        main_module.azure_service = previous_global
