"""Route contract and endpoint behavioral guard tests.

These tests are designed to fail loudly if:
- A public endpoint path changes
- An HTTP method changes
- A required field in a representative JSON response disappears

Update EXPECTED_ROUTES intentionally if you add/remove endpoints.
"""
from fastapi.routing import APIRoute
import main as main_module
from fastapi.testclient import TestClient

EXPECTED_ROUTES = {
    # path: set(methods)
    '/': {'GET'},
    '/healthz': {'GET'},
    '/favicon.ico': {'GET'},
    '/v1/data': {'GET'},
    '/v1/data/{translation_id}': {'GET'},
    '/v1/data/{translation_id}/random': {'GET'},
    '/v1/data/{translation_id}/random/{book_id}': {'GET'},
    '/v1/data/{translation_id}/{book_id}': {'GET'},
    '/v1/data/{translation_id}/{book_id}/{chapter}': {'GET'},
    '/{ref:path}': {'GET'},
}

# Routes we intentionally ignore (FastAPI system docs/openapi)
IGNORED = {'/openapi.json', '/docs', '/redoc', '/docs/oauth2-redirect'}


def test_route_set_has_not_changed():
    route_map = {}
    for r in main_module.app.routes:
        if isinstance(r, APIRoute):
            if r.path in IGNORED:
                continue
            route_map[r.path] = set(r.methods) - {'HEAD', 'OPTIONS'}  # HEAD auto-added

    assert set(route_map.keys()) == set(EXPECTED_ROUTES.keys()), (
        "Route paths changed. Update EXPECTED_ROUTES if intentional.\n"
        f"Current: {sorted(route_map.keys())}\nExpected: {sorted(EXPECTED_ROUTES.keys())}"
    )

    for path, methods in EXPECTED_ROUTES.items():
        assert route_map[path] == methods, f"Methods for {path} changed: {route_map[path]} != {methods}"


def test_health_endpoint():
    client = TestClient(main_module.app)
    r = client.get('/healthz')
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_favicon_endpoint():
    client = TestClient(main_module.app)
    r = client.get('/favicon.ico')
    # Either 200 (file present) or 204 (missing -> intentionally quiet)
    assert r.status_code in (200, 204)


def test_reference_404_on_unknown_book():
    client = TestClient(main_module.app)
    r = client.get('/NotABook+1:1')
    assert r.status_code == 404


def test_translation_not_found_triggers_404(fake_service):
    client = TestClient(main_module.app)
    # Use a valid reference but invalid translation query param
    r = client.get('/John+3:16?translation=doesnotexist')
    assert r.status_code == 404


def test_random_root_json_contract(fake_service):
    client = TestClient(main_module.app)
    r = client.get('/?random=true')
    assert r.status_code == 200
    body = r.json()
    for key in ['reference', 'verses', 'text', 'translation_id']:
        assert key in body, f"Missing key '{key}' in random root response"
    assert isinstance(body['verses'], list) and body['verses'], "Verses list empty"
