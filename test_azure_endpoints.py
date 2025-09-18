#!/usr/bin/env python3
"""
Simple test script to check Azure service functionality
"""

import asyncio
from app.services.azure_xml_service import AzureXMLBibleService

async def test_azure_service():
    try:
        print("Initializing Azure service...")
        service = AzureXMLBibleService()
        
        print("Listing translations...")
        translations = service.list_translations()
        print(f"Found {len(translations)} translations:")
        for trans in translations[:3]:  # Show first 3
            print(f"  - {trans['identifier']}: {trans['name']} ({trans['language']})")
        
        if translations:
            # Test getting verses from first translation
            first_trans = translations[0]['identifier']
            print(f"\nTesting verses from {first_trans}...")
            verses = service.get_verses_by_reference(first_trans, 'JHN', 3, 16, 16)
            if verses:
                print(f"John 3:16 - {verses[0]['text'][:100]}...")
            else:
                print("No verses found for John 3:16")
        
        print("\nAzure service test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error testing Azure service: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_azure_service())