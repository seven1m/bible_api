"""Tests for versioned /v1/data endpoints (translation discovery & random verses)."""
import pytest
from fastapi.testclient import TestClient
import main as main_module

@pytest.fixture()
def client() -> TestClient:  # override to ensure fresh client if needed
    return TestClient(main_module.app)

def test_list_translations(client: TestClient):
    resp = client.get('/v1/data')
    assert resp.status_code == 200
    data = resp.json()
    assert 'translations' in data and len(data['translations']) == 1
    t = data['translations'][0]
    assert t['identifier'] == 'test'
    assert t['url'].endswith('/v1/data/test')


def test_get_translation_books(client: TestClient):
    resp = client.get('/v1/data/test')
    assert resp.status_code == 200
    data = resp.json()
    assert data['translation']['identifier'] == 'test'
    assert any(b['id'] == 'JHN' for b in data['books'])


def test_random_verse(client: TestClient):
    resp = client.get('/v1/data/test/random')
    assert resp.status_code == 200
    data = resp.json()
    assert data['translation']['identifier'] == 'test'
    verse = data['random_verse']
    assert verse['book_id'] in ['JHN', 'GEN']


def test_random_verse_by_book(client: TestClient):
    resp = client.get('/v1/data/test/random/JHN')
    assert resp.status_code == 200
    verse = resp.json()['random_verse']
    assert verse['book_id'] == 'JHN'


def test_book_chapters(client: TestClient):
    resp = client.get('/v1/data/test/JHN')
    assert resp.status_code == 200
    chapters = resp.json()['chapters']
    assert any(c['chapter'] == 3 for c in chapters)


def test_chapter_verses(client: TestClient):
    resp = client.get('/v1/data/test/JHN/3')
    assert resp.status_code == 200
    verses = resp.json()['verses']
    assert len(verses) >= 2


def test_chapter_not_found(client: TestClient):
    resp = client.get('/v1/data/test/JHN/99')
    assert resp.status_code == 404
