"""Pytest fixtures for the Bible API test suite.

Provides:
- FakeAzureXMLBibleService: deterministic in-memory replacement for AzureXMLBibleService
- FastAPI test client (sync) via httpx.AsyncClient for async endpoints
- Dependency overrides for both router dependency (get_xml_service) and global main.azure_service
"""
from __future__ import annotations

import pytest
from typing import List, Dict, Any, Optional
from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys, os, pathlib

# --- Ensure project root on sys.path (robust when running from tests/ dir) ---
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import application modules (after path adjustment)
import main as main_module
from app.services.providers import get_xml_service as real_get_xml_service
from app.services.azure_xml_service import AzureXMLBibleService

# ----------------------
# Fake Service
# ----------------------
class FakeAzureXMLBibleService(AzureXMLBibleService):  # type: ignore
    """In-memory stand-in implementing just the interface used in tests.

    This does NOT touch Azure; it constructs small deterministic datasets.
    """
    def __init__(self):  # no super().__init__ (avoid Azure client)
        self._available_translations = [
            {
                'identifier': 'test',
                'name': 'Test Translation',
                'language': 'english',
                'language_code': 'en',
                'license': 'Public Domain',
                'file_path': 'unused.xml'
            }
        ]
        self._translation_cache = {t['identifier']: t for t in self._available_translations}
        # Small verse corpus (John 3:16-17, Genesis 1:1)
        self._verses = {
            ('test', 'JHN', 3): [
                {
                    'id': 1,
                    'book_id': 'JHN', 'book': 'John', 'chapter': 3, 'verse': 16,
                    'text': 'For God so loved the world.' , 'translation_id': 'test'
                },
                {
                    'id': 2,
                    'book_id': 'JHN', 'book': 'John', 'chapter': 3, 'verse': 17,
                    'text': 'For God did not send his Son to condemn.', 'translation_id': 'test'
                },
            ],
            ('test', 'GEN', 1): [
                {
                    'id': 3,
                    'book_id': 'GEN', 'book': 'Genesis', 'chapter': 1, 'verse': 1,
                    'text': 'In the beginning God created the heavens and the earth.', 'translation_id': 'test'
                }
            ]
        }

    # Minimal method implementations
    def list_translations(self) -> List[Dict[str, Any]]:
        return self._available_translations

    def get_translation_info(self, identifier: str) -> Optional[Dict[str, Any]]:
        return self._translation_cache.get(identifier.lower())

    def get_books_for_translation(self, translation_id: str) -> List[Dict[str, str]]:
        return [
            {'id': 'JHN', 'name': 'John'},
            {'id': 'GEN', 'name': 'Genesis'}
        ]

    def get_chapters_for_book(self, translation_id: str, book: str):
        chapters = []
        for (tid, b, ch), verses in self._verses.items():
            if tid == translation_id and b == book:
                chapters.append({'book_id': b, 'book_name': verses[0]['book'], 'chapter': ch})
        return chapters

    def get_verses_by_reference(self, translation_id: str, book: str, chapter: int, verse_start: int | None = None, verse_end: int | None = None):
        verses = self._verses.get((translation_id, book, chapter), [])
        if verse_start is None and verse_end is None:
            return verses
        sel = []
        for v in verses:
            if verse_start is not None and v['verse'] < verse_start:
                continue
            if verse_end is not None and v['verse'] > verse_end:
                continue
            sel.append(v)
        return sel

    def get_random_verse(self, translation_id: str, books: Optional[List[str]] = None):
        # Just return first verse matching constraints for determinism
        for (tid, b, ch), verses in self._verses.items():
            if tid != translation_id:
                continue
            if books and b not in books:
                continue
            return verses[0]
        return None

# ----------------------
# Fixtures
# ----------------------
@pytest.fixture(scope="session")
def fake_service() -> FakeAzureXMLBibleService:
    return FakeAzureXMLBibleService()

@pytest.fixture(autouse=True)
def override_dependencies(request, fake_service: FakeAzureXMLBibleService):
    """Override DI points before each test.
    Sets both providers.get_xml_service and main.azure_service.
    """
    # If test requests real Azure (marked with @pytest.mark.azure), do not override
    if request.node.get_closest_marker('azure'):
        # For azure tests we skip overriding but must still yield to satisfy fixture protocol
        yield
        return
    # Patch dependency override for router-based Depends(get_xml_service)
    from app import services as services_pkg  # type: ignore
    from app.services import providers as providers_module  # ensure module loaded

    def _get_xml_service_override():
        return fake_service

    # FastAPI style override (in case we add dependency injection through app.dependency_overrides)
    main_module.app.dependency_overrides[real_get_xml_service] = _get_xml_service_override

    # Set global azure_service used in main helpers & routes
    main_module.azure_service = fake_service

    try:
        yield
    finally:
        # Cleanup
        main_module.app.dependency_overrides.pop(real_get_xml_service, None)

@pytest.fixture()
def client() -> TestClient:
    return TestClient(main_module.app)
