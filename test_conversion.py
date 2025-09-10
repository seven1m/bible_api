#!/usr/bin/env python3
"""
Simple test script for the Bible API Python conversion.
This tests basic functionality without requiring a full database setup.
"""

import sys
import os
sys.path.append('.')

def test_imports():
    """Test that all modules can be imported successfully"""
    print("Testing imports...")
    
    try:
        from main import app
        print("✓ FastAPI app imports successfully")
    except Exception as e:
        print(f"✗ Failed to import FastAPI app: {e}")
        return False
    
    try:
        from import_bible import BibleImporter
        print("✓ Bible importer imports successfully")
    except Exception as e:
        print(f"✗ Failed to import Bible importer: {e}")
        return False
    
    return True

def test_bible_reference_parsing():
    """Test the Bible reference parsing functionality"""
    print("\nTesting Bible reference parsing...")
    
    from main import parse_bible_reference
    
    test_cases = [
        ("John 3:16", True),
        ("Matt 5:1-10", True),
        ("Genesis 1:1", True),
        ("Ps 23:1", True),
        ("invalid reference", False),
        ("", False),
    ]
    
    passed = 0
    for ref, should_pass in test_cases:
        try:
            result = parse_bible_reference(ref)
            if should_pass and result:
                print(f"✓ '{ref}' parsed successfully: {result}")
                passed += 1
            elif not should_pass and not result:
                print(f"✓ '{ref}' correctly failed to parse")
                passed += 1
            else:
                print(f"✗ '{ref}' parsing result unexpected: {result}")
        except Exception as e:
            if not should_pass:
                print(f"✓ '{ref}' correctly failed with error: {e}")
                passed += 1
            else:
                print(f"✗ '{ref}' failed unexpectedly: {e}")
    
    print(f"Bible reference parsing: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)

def test_app_routes():
    """Test that FastAPI routes are properly configured"""
    print("\nTesting app routes...")
    
    from main import app
    
    expected_routes = [
        "/",
        "/data",
        "/data/{translation_id}",
        "/data/{translation_id}/random",
        "/data/{translation_id}/random/{book_id}",
        "/data/{translation_id}/{book_id}",
        "/data/{translation_id}/{book_id}/{chapter}",
        "/{ref:path}",
    ]
    
    actual_routes = []
    for route in app.routes:
        if hasattr(route, 'path') and route.path not in ['/openapi.json', '/docs', '/redoc', '/docs/oauth2-redirect']:
            actual_routes.append(route.path)
    
    missing_routes = []
    for expected in expected_routes:
        if expected not in actual_routes:
            missing_routes.append(expected)
    
    if missing_routes:
        print(f"✗ Missing routes: {missing_routes}")
        return False
    else:
        print(f"✓ All expected routes present: {len(expected_routes)} routes")
        return True

def test_data_models():
    """Test database model definitions"""
    print("\nTesting data models...")
    
    try:
        from main import Translation, Verse, Base
        
        # Check that models have expected attributes
        translation_attrs = ['id', 'identifier', 'name', 'language', 'language_code', 'license']
        verse_attrs = ['id', 'book_num', 'book_id', 'book', 'chapter', 'verse', 'text', 'translation_id']
        
        for attr in translation_attrs:
            if not hasattr(Translation, attr):
                print(f"✗ Translation model missing attribute: {attr}")
                return False
        
        for attr in verse_attrs:
            if not hasattr(Verse, attr):
                print(f"✗ Verse model missing attribute: {attr}")
                return False
        
        print("✓ Database models have all expected attributes")
        return True
    
    except Exception as e:
        print(f"✗ Error testing data models: {e}")
        return False

def test_template_exists():
    """Test that templates exist"""
    print("\nTesting templates...")
    
    template_files = ['templates/index.html']
    
    for template in template_files:
        if os.path.exists(template):
            print(f"✓ Template exists: {template}")
        else:
            print(f"✗ Template missing: {template}")
            return False
    
    return True

def main():
    """Run all tests"""
    print("Bible API Python Conversion - Basic Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_bible_reference_parsing,
        test_app_routes,
        test_data_models,
        test_template_exists,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test_func.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed! The Python conversion appears to be working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())