"""Unit tests for helper functions in main.py.

Covers:
- parse_bible_reference happy paths & failures
- render_verse_response assembly and verse_numbers flag through public function
- get_translation default selection (using fake service)
"""
from typing import List, Dict
import pytest
import main as main_module

parse_bible_reference = main_module.parse_bible_reference
render_verse_response = main_module.render_verse_response
get_translation = main_module.get_translation

# ----------------------
# parse_bible_reference
# ----------------------
@pytest.mark.parametrize(
    "ref,expected_book,expected_chapter,expected_from,expected_to",
    [
        ("John 3:16", 'JHN', 3, 16, 16),
        ("Matt 5:1-10", 'MAT', 5, 1, 10),
        ("Genesis 1:1", 'GEN', 1, 1, 1),
        ("Ps 23:1", 'PSA', 23, 1, 1),
    ]
)
def test_parse_bible_reference_success(ref, expected_book, expected_chapter, expected_from, expected_to):
    ranges = parse_bible_reference(ref)
    assert ranges is not None
    (ref_from, ref_to) = ranges[0]
    assert ref_from['book'] == expected_book
    assert ref_from['chapter'] == expected_chapter
    assert ref_from['verse'] == expected_from
    assert ref_to['verse'] == expected_to

@pytest.mark.parametrize("ref", ["", "NotARef", "Jn", "John3:16", "John 3", "1 Unknown 5:1"])
def test_parse_bible_reference_fail(ref):
    assert parse_bible_reference(ref) is None

# ----------------------
# render_verse_response
# ----------------------

def _make_translation():
    return {
        'identifier': 'test', 'name': 'Test Translation', 'language': 'english',
        'language_code': 'en', 'license': 'Public Domain'
    }

def test_render_verse_response_basic():
    verses = [
        {'book_id': 'JHN', 'book': 'John', 'chapter': 3, 'verse': 16, 'text': 'For God so loved.'},
        {'book_id': 'JHN', 'book': 'John', 'chapter': 3, 'verse': 17, 'text': 'For God did not send.'},
    ]
    resp = render_verse_response(verses, 'John 3:16-17', _make_translation())
    assert resp['reference'] == 'John 3:16-17'
    # Text concatenated without verse numbers by default
    assert resp['text'] == 'For God so loved.For God did not send.'
    assert len(resp['verses']) == 2


def test_render_verse_response_with_numbers():
    verses = [
        {'book_id': 'JHN', 'book': 'John', 'chapter': 3, 'verse': 16, 'text': 'For God so loved.'},
    ]
    resp = render_verse_response(verses, 'John 3:16', _make_translation(), verse_numbers=True)
    assert resp['text'].startswith('(16)')

# ----------------------
# get_translation default selection
# ----------------------

def test_get_translation_defaults_to_first(fake_service):
    # Passing None chooses the first (only) translation from fake service
    t = get_translation(None)
    assert t['identifier'] == 'test'
