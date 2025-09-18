"""Tests covering root page, random verse via root, and dynamic reference endpoint."""
from fastapi.testclient import TestClient
import main as main_module


def test_root_html(client: TestClient):
    resp = client.get('/')
    # root returns HTML unless random param present
    assert resp.status_code == 200
    # Basic sanity check for HTML content
    assert 'text/html' in resp.headers.get('content-type', '')


def test_root_random_json(client: TestClient):
    resp = client.get('/?random=true')
    assert resp.status_code == 200
    data = resp.json()
    assert data['translation_id'] == 'test'


def test_reference_endpoint_success(client: TestClient):
    resp = client.get('/John+3:16')
    assert resp.status_code == 200
    data = resp.json()
    assert data['reference'] == 'John 3:16'
    assert data['translation_id'] == 'test'


def test_reference_endpoint_not_found(client: TestClient):
    resp = client.get('/Unknown+1:1')
    assert resp.status_code == 404


def test_reference_endpoint_verse_numbers(client: TestClient):
    resp = client.get('/John+3:16?verse_numbers=true')
    assert resp.status_code == 200
    data = resp.json()
    assert data['text'].startswith('(16)')
