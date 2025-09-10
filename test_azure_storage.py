#!/usr/bin/env python3
"""
Test script for Azure Blob Storage integration.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_azure_import():
    """Test that the Azure Blob Storage imports work"""
    print("Testing Azure Blob Storage imports...")
    
    try:
        from import_bible import BibleImporter, AZURE_AVAILABLE
        print("✓ BibleImporter imports successfully")
        
        if AZURE_AVAILABLE:
            print("✓ Azure Blob Storage SDK is available")
        else:
            print("✗ Azure Blob Storage SDK not available")
            return False
            
        return True
    except Exception as e:
        print(f"✗ Failed to import: {e}")
        return False

def test_azure_configuration():
    """Test Azure Blob Storage configuration"""
    print("\nTesting Azure Blob Storage configuration...")
    
    # Mock database URL for testing
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    from import_bible import BibleImporter
    
    try:
        importer = BibleImporter('sqlite:///:memory:')
        
        if importer.blob_service_client:
            print("✓ Azure Blob Storage client initialized successfully")
            print(f"✓ Container name: {importer.container_name}")
            return True
        else:
            print("○ Azure Blob Storage not configured (expected without credentials)")
            print("  To configure Azure Blob Storage, set one of:")
            print("  - AZURE_STORAGE_CONNECTION_STRING")
            print("  - AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY")
            print("  - AZURE_STORAGE_CONTAINER_NAME (optional, defaults to 'bibles')")
            return True
            
    except Exception as e:
        print(f"✗ Error initializing BibleImporter: {e}")
        return False

def test_file_listing():
    """Test file listing functionality"""
    print("\nTesting file listing functionality...")
    
    # Mock database URL for testing
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    from import_bible import BibleImporter
    
    try:
        importer = BibleImporter('sqlite:///:memory:')
        
        # Test with local files
        files = importer.list_bible_files('./bibles')
        print(f"✓ Found {len(files)} files in local bibles directory")
        
        if files:
            # Show first few files as examples
            for i, (file_path, filename) in enumerate(files[:3]):
                print(f"  {i+1}. {filename}")
            if len(files) > 3:
                print(f"  ... and {len(files) - 3} more")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing file listing: {e}")
        return False

def test_environment_variables():
    """Test environment variable configuration"""
    print("\nTesting environment variables...")
    
    # Check for Azure configuration
    azure_connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    azure_account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    azure_account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'bibles')
    
    if azure_connection_string:
        print("✓ AZURE_STORAGE_CONNECTION_STRING is set")
        return True
    elif azure_account_name and azure_account_key:
        print("✓ AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY are set")
        return True
    else:
        print("○ Azure credentials not configured (will use local files)")
        print("  To use Azure Blob Storage, set one of:")
        print("    AZURE_STORAGE_CONNECTION_STRING")
        print("    OR")
        print("    AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY")
        print(f"  Container name will be: {container_name}")
        return True

def main():
    """Run all tests"""
    print("Bible API - Azure Blob Storage Integration Tests")
    print("=" * 55)
    
    tests = [
        test_azure_import,
        test_azure_configuration,
        test_environment_variables,
        test_file_listing,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test_func.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 55)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Azure Blob Storage tests passed!")
        print("\nNext steps:")
        print("1. Configure Azure Blob Storage credentials")
        print("2. Upload XML files to your Azure Blob Storage container")
        print("3. Run the import script with your configured storage")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())