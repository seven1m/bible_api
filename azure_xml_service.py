#!/usr/bin/env python3
"""
Azure XML Bible Service - Replaces database operations with direct XML file reading from Azure Blob Storage
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
import os
import re
import random
from dotenv import load_dotenv

load_dotenv()

class AzureXMLBibleService:
    """Service to read Bible data directly from XML files in Azure Blob Storage"""
    
    def __init__(self):
        """Initialize Azure Blob Storage client"""
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.container_name = os.getenv('AZURE_CONTAINER_NAME', 'bible-translations')
        
        if not self.connection_string:
            raise Exception("AZURE_STORAGE_CONNECTION_STRING environment variable is required")
        
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
        except Exception as e:
            raise Exception(f"Failed to connect to Azure Blob Storage: {e}")
        
        # Cache for parsed XML data to avoid re-parsing
        self._xml_cache = {}
        self._translation_cache = {}
        self._available_translations = None
    
    def _get_xml_content(self, file_path: str) -> Optional[str]:
        """Get XML content from Azure blob with caching"""
        if file_path in self._xml_cache:
            return self._xml_cache[file_path]
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=file_path
            )
            content = blob_client.download_blob().readall().decode('utf-8')
            self._xml_cache[file_path] = content
            return content
        except ResourceNotFoundError:
            return None
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    
    def _parse_xml_for_translation_info(self, xml_content: str, identifier: str) -> Dict[str, str]:
        """Extract translation metadata from XML"""
        try:
            root = ET.fromstring(xml_content)
            
            # Try to extract translation info from various XML formats
            name = identifier.upper()
            license_text = "Public Domain"
            language = "english"
            language_code = "en"
            
            # Check for OSIS format
            if root.tag.endswith('osis'):
                work = root.find('.//{http://www.bibletechnologies.net/2003/OSIS/namespace}work')
                if work is not None:
                    title_elem = work.find('.//{http://www.bibletechnologies.net/2003/OSIS/namespace}title')
                    if title_elem is not None:
                        name = title_elem.text or name
                    
                    rights_elem = work.find('.//{http://www.bibletechnologies.net/2003/OSIS/namespace}rights')
                    if rights_elem is not None:
                        license_text = rights_elem.text or license_text
            
            # Check for other XML formats
            elif 'title' in root.attrib:
                name = root.attrib['title']
            elif 'name' in root.attrib:
                name = root.attrib['name']
            
            # Determine language from file path or content
            if 'romanian' in identifier.lower() or 'ro-' in identifier.lower():
                language = "romanian"
                language_code = "ro"
            
            return {
                'identifier': identifier,
                'name': name,
                'language': language,
                'language_code': language_code,
                'license': license_text
            }
            
        except ET.ParseError:
            # Return basic info if XML parsing fails
            return {
                'identifier': identifier,
                'name': identifier.upper(),
                'language': 'romanian' if 'romanian' in identifier.lower() else 'english',
                'language_code': 'ro' if 'romanian' in identifier.lower() else 'en',
                'license': 'Unknown'
            }
    
    def list_translations(self) -> List[Dict[str, str]]:
        """List all available Bible translations from both language folders"""
        if self._available_translations is not None:
            return self._available_translations
        
        translations = []
        
        try:
            # List all blobs in the container
            blob_list = self.container_client.list_blobs()
            
            for blob in blob_list:
                if blob.name.endswith('.xml'):
                    # Extract identifier from filename
                    if '/' in blob.name:
                        filename = blob.name.split('/')[-1]
                    else:
                        filename = blob.name
                    
                    identifier = filename.replace('.xml', '').lower()
                    
                    # Get translation info by parsing XML
                    xml_content = self._get_xml_content(blob.name)
                    if xml_content:
                        trans_info = self._parse_xml_for_translation_info(xml_content, identifier)
                        trans_info['file_path'] = blob.name
                        translations.append(trans_info)
                        
                        # Cache the translation info
                        self._translation_cache[identifier] = trans_info
            
            self._available_translations = translations
            return translations
            
        except Exception as e:
            print(f"Error listing translations: {e}")
            return []
    
    def get_translation_info(self, identifier: str) -> Optional[Dict[str, str]]:
        """Get translation metadata by identifier"""
        identifier = identifier.lower()
        
        if identifier in self._translation_cache:
            return self._translation_cache[identifier]
        
        # Refresh translations list if not cached
        translations = self.list_translations()
        
        for trans in translations:
            if trans['identifier'] == identifier:
                return trans
        
        return None
    
    def _normalize_book_id(self, book_input: str) -> str:
        """Normalize book names/IDs to standard 3-letter codes"""
        book_input = book_input.upper().strip()
        
        # Direct 3-letter codes
        if len(book_input) == 3:
            return book_input
        
        # Common book name mappings
        book_mapping = {
            'GENESIS': 'GEN', 'EXODUS': 'EXO', 'LEVITICUS': 'LEV', 'NUMBERS': 'NUM', 'DEUTERONOMY': 'DEU',
            'JOSHUA': 'JOS', 'JUDGES': 'JDG', 'RUTH': 'RUT', '1SAMUEL': '1SA', '2SAMUEL': '2SA',
            '1KINGS': '1KI', '2KINGS': '2KI', '1CHRONICLES': '1CH', '2CHRONICLES': '2CH', 'EZRA': 'EZR',
            'NEHEMIAH': 'NEH', 'ESTHER': 'EST', 'JOB': 'JOB', 'PSALMS': 'PSA', 'PROVERBS': 'PRO',
            'ECCLESIASTES': 'ECC', 'SONGOFSOLOMON': 'SNG', 'ISAIAH': 'ISA', 'JEREMIAH': 'JER', 'LAMENTATIONS': 'LAM',
            'EZEKIEL': 'EZK', 'DANIEL': 'DAN', 'HOSEA': 'HOS', 'JOEL': 'JOL', 'AMOS': 'AMO',
            'OBADIAH': 'OBA', 'JONAH': 'JON', 'MICAH': 'MIC', 'NAHUM': 'NAH', 'HABAKKUK': 'HAB',
            'ZEPHANIAH': 'ZEP', 'HAGGAI': 'HAG', 'ZECHARIAH': 'ZEC', 'MALACHI': 'MAL',
            'MATTHEW': 'MAT', 'MARK': 'MRK', 'LUKE': 'LUK', 'JOHN': 'JHN', 'ACTS': 'ACT',
            'ROMANS': 'ROM', '1CORINTHIANS': '1CO', '2CORINTHIANS': '2CO', 'GALATIANS': 'GAL', 'EPHESIANS': 'EPH',
            'PHILIPPIANS': 'PHP', 'COLOSSIANS': 'COL', '1THESSALONIANS': '1TH', '2THESSALONIANS': '2TH', 
            '1TIMOTHY': '1TI', '2TIMOTHY': '2TI', 'TITUS': 'TIT', 'PHILEMON': 'PHM', 'HEBREWS': 'HEB', 
            'JAMES': 'JAS', '1PETER': '1PE', '2PETER': '2PE', '1JOHN': '1JN', '2JOHN': '2JN', 
            '3JOHN': '3JN', 'JUDE': 'JUD', 'REVELATION': 'REV',
            
            # Common abbreviations
            'MATT': 'MAT', 'PHIL': 'PHP', 'PROV': 'PRO', 'ECCL': 'ECC', 'SONG': 'SNG',
            'ISA': 'ISA', 'JER': 'JER', 'LAM': 'LAM', 'EZEK': 'EZK', 'DAN': 'DAN',
            'JON': 'JON', 'MIC': 'MIC', 'NAH': 'NAH', 'HAB': 'HAB', 'ZEP': 'ZEP',
            'HAG': 'HAG', 'ZEC': 'ZEC', 'MAL': 'MAL', 'REV': 'REV'
        }
        
        return book_mapping.get(book_input.replace(' ', ''), book_input[:3])
    
    def _find_book_in_xml(self, root: ET.Element, book_id: str) -> Optional[ET.Element]:
        """Find a book element in XML by various possible identifiers"""
        book_id_normalized = self._normalize_book_id(book_id)
        
        # Try different ways to find the book
        search_patterns = [
            f".//*[@osisID='{book_id}']",
            f".//*[@osisID='{book_id_normalized}']",
            f".//*[@id='{book_id}']",
            f".//*[@id='{book_id_normalized}']",
            f".//book[@id='{book_id}']",
            f".//book[@id='{book_id_normalized}']"
        ]
        
        for pattern in search_patterns:
            book_elem = root.find(pattern)
            if book_elem is not None:
                return book_elem
        
        # If not found by ID, try by name
        for book_elem in root.findall('.//book'):
            name = book_elem.get('name', '').upper()
            if book_id_normalized in name or name.startswith(book_id_normalized):
                return book_elem
        
        return None
    
    def get_verses_by_reference(self, translation_id: str, book: str, chapter: int, 
                               verse_start: Optional[int] = None, verse_end: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get verses by book, chapter, and verse range"""
        translation = self.get_translation_info(translation_id)
        if not translation:
            return []

        xml_content = self._get_xml_content(translation['file_path'])
        if not xml_content:
            return []

        try:
            root = ET.fromstring(xml_content)
            verses = []
            
            # Find the book - handle USFX format
            book_id_normalized = self._normalize_book_id(book)
            book_element = None
            
            # Try USFX format first
            book_element = root.find(f".//book[@id='{book}']")
            if not book_element:
                book_element = root.find(f".//book[@id='{book_id_normalized}']")
            
            # Fallback to other formats
            if not book_element:
                book_element = self._find_book_in_xml(root, book)
            
            if not book_element:
                return []
            
            # Get book name and ID
            book_name = book_element.get('name', book)
            book_id = book_element.get('id', book_id_normalized)
            
            # Handle USFX format
            if root.tag == 'usfx' or 'usfx' in root.tag:
                # USFX format: verses are marked with <v id="N"/> tags
                current_chapter = None
                current_verse = None
                verse_text = ""
                
                # Iterate through all elements in the book
                for elem in book_element.iter():
                    if elem.tag == 'c' and 'id' in elem.attrib:
                        # Chapter marker
                        try:
                            current_chapter = int(elem.attrib['id'])
                        except ValueError:
                            continue
                    elif elem.tag == 'v' and 'id' in elem.attrib:
                        # Verse marker - save previous verse if exists
                        if (current_chapter == chapter and current_verse is not None and 
                            verse_text.strip() and 
                            (verse_start is None or current_verse >= verse_start) and
                            (verse_end is None or current_verse <= verse_end)):
                            
                            verses.append({
                                'id': len(verses) + 1,
                                'book_id': book_id,
                                'book': book_name,
                                'chapter': chapter,
                                'verse': current_verse,
                                'text': verse_text.strip(),
                                'translation_id': translation['identifier']
                            })
                        
                        # Start new verse
                        try:
                            current_verse = int(elem.attrib['id'])
                            verse_text = ""
                        except ValueError:
                            continue
                    elif current_chapter == chapter and current_verse is not None:
                        # Collect text for current verse
                        if elem.text:
                            verse_text += elem.text
                        if elem.tail:
                            verse_text += elem.tail
                
                # Don't forget the last verse
                if (current_chapter == chapter and current_verse is not None and 
                    verse_text.strip() and 
                    (verse_start is None or current_verse >= verse_start) and
                    (verse_end is None or current_verse <= verse_end)):
                    
                    verses.append({
                        'id': len(verses) + 1,
                        'book_id': book_id,
                        'book': book_name,
                        'chapter': chapter,
                        'verse': current_verse,
                        'text': verse_text.strip(),
                        'translation_id': translation['identifier']
                    })
            
            else:
                # Handle other XML formats (OSIS, standard chapter/verse)
                verse_elements = []
                
                # Try OSIS format first - use a simpler approach
                chapter_prefix = f"{book_id}.{chapter}."
                osis_verses = []
                
                # Find all elements with osisID attribute
                for elem in root.iter():
                    osis_id = elem.get('osisID')
                    if osis_id and osis_id.startswith(chapter_prefix):
                        osis_verses.append(elem)
                
                if osis_verses:
                    # OSIS format
                    for verse_elem in osis_verses:
                        osis_id = verse_elem.get('osisID', '')
                        parts = osis_id.split('.')
                        if len(parts) >= 3:
                            try:
                                verse_num = int(parts[2])
                                if verse_start and verse_num < verse_start:
                                    continue
                                if verse_end and verse_num > verse_end:
                                    continue
                                
                                # Get verse text
                                text = verse_elem.text or ''
                                if not text:
                                    # Try to get text from child elements
                                    text = ''.join(verse_elem.itertext())
                                
                                verses.append({
                                    'id': len(verses) + 1,
                                    'book_id': book_id,
                                    'book': book_name,
                                    'chapter': chapter,
                                    'verse': verse_num,
                                    'text': text.strip(),
                                    'translation_id': translation['identifier']
                                })
                            except ValueError:
                                continue
                else:
                    # Try standard chapter/verse structure
                    chapter_elem = book_element.find(f".//chapter[@number='{chapter}']")
                    if chapter_elem is not None:
                        for verse_elem in chapter_elem.findall('verse'):
                            try:
                                verse_num = int(verse_elem.get('number', 0))
                                if verse_start and verse_num < verse_start:
                                    continue
                                if verse_end and verse_num > verse_end:
                                    continue
                                
                                text = verse_elem.text or ''
                                if not text:
                                    text = ''.join(verse_elem.itertext())
                                
                                verses.append({
                                    'id': len(verses) + 1,
                                    'book_id': book_id,
                                    'book': book_name,
                                    'chapter': chapter,
                                    'verse': verse_num,
                                    'text': text.strip(),
                                    'translation_id': translation['identifier']
                                })
                            except ValueError:
                                continue
            
            return sorted(verses, key=lambda x: x['verse'])
            
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
            return []
    
    def get_chapters_for_book(self, translation_id: str, book: str) -> List[Dict[str, Any]]:
        """Get available chapters for a book"""
        translation = self.get_translation_info(translation_id)
        if not translation:
            return []

        xml_content = self._get_xml_content(translation['file_path'])
        if not xml_content:
            return []

        try:
            root = ET.fromstring(xml_content)
            chapters = []
            
            # Find the book - handle USFX format
            book_id_normalized = self._normalize_book_id(book)
            book_element = None
            
            # Try USFX format first
            book_element = root.find(f".//book[@id='{book}']")
            if not book_element:
                book_element = root.find(f".//book[@id='{book_id_normalized}']")
            
            # Fallback to other formats
            if not book_element:
                book_element = self._find_book_in_xml(root, book)
            
            if not book_element:
                return []
            
            # Get book name and ID
            book_name = book_element.get('name', book)
            book_id = book_element.get('id', book_id_normalized)
            
            # Handle USFX format
            if root.tag == 'usfx' or 'usfx' in root.tag:
                # USFX format: chapters are marked with <c id="N"/> tags
                chapters_found = set()
                
                # Iterate through all elements in the book to find chapter markers
                for elem in book_element.iter():
                    if elem.tag == 'c' and 'id' in elem.attrib:
                        try:
                            chapter_num = int(elem.attrib['id'])
                            chapters_found.add(chapter_num)
                        except ValueError:
                            continue
                
                # Create chapter list
                for chapter_num in sorted(chapters_found):
                    chapters.append({
                        'book_id': book_id,
                        'book_name': book_name,
                        'chapter': chapter_num
                    })
            
            else:
                # Handle other XML formats (OSIS, standard chapter/verse)
                # Try OSIS format first
                for elem in root.iter():
                    osis_id = elem.get('osisID')
                    if osis_id and osis_id.startswith(f"{book_id}."):
                        parts = osis_id.split('.')
                        if len(parts) >= 2:
                            try:
                                chapter_num = int(parts[1])
                                chapters.append({
                                    'book_id': book_id,
                                    'book_name': book_name,
                                    'chapter': chapter_num
                                })
                            except ValueError:
                                continue
                
                # If no OSIS chapters found, try standard structure
                if not chapters:
                    for chapter_elem in book_element.findall('.//chapter'):
                        try:
                            chapter_num = int(chapter_elem.get('number', 0))
                            chapters.append({
                                'book_id': book_id,
                                'book_name': book_name,
                                'chapter': chapter_num
                            })
                        except ValueError:
                            continue
            
            # Remove duplicates and sort
            seen = set()
            unique_chapters = []
            for chapter in chapters:
                chapter_num = chapter['chapter']
                if chapter_num not in seen:
                    seen.add(chapter_num)
                    unique_chapters.append(chapter)
            
            return sorted(unique_chapters, key=lambda x: x['chapter'])
            
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
            return []
    
    def get_random_verse(self, translation_id: str, books: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get a random verse from the specified translation"""
        translation = self.get_translation_info(translation_id)
        if not translation:
            return None
        
        xml_content = self._get_xml_content(translation['file_path'])
        if not xml_content:
            return None
        
        try:
            root = ET.fromstring(xml_content)
            all_verses = []
            
            # Collect all verses from specified books or all books
            for book_elem in root.findall('.//book'):
                book_id = book_elem.get('id', '')
                book_name = book_elem.get('name', book_id)
                
                # Filter by books if specified
                if books:
                    book_id_normalized = self._normalize_book_id(book_id)
                    if book_id_normalized not in [self._normalize_book_id(b) for b in books]:
                        continue
                
                # Get verses from this book
                for chapter_elem in book_elem.findall('.//chapter'):
                    try:
                        chapter_num = int(chapter_elem.get('number', 0))
                        for verse_elem in chapter_elem.findall('verse'):
                            try:
                                verse_num = int(verse_elem.get('number', 0))
                                text = verse_elem.text or ''.join(verse_elem.itertext())
                                
                                if text.strip():
                                    all_verses.append({
                                        'book_id': book_id,
                                        'book': book_name,
                                        'chapter': chapter_num,
                                        'verse': verse_num,
                                        'text': text.strip()
                                    })
                            except ValueError:
                                continue
                    except ValueError:
                        continue
            
            return random.choice(all_verses) if all_verses else None
            
        except ET.ParseError:
            return None
    
    def search_verses(self, translation_id: str, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for verses containing the query text"""
        translation = self.get_translation_info(translation_id)
        if not translation:
            return []
        
        xml_content = self._get_xml_content(translation['file_path'])
        if not xml_content:
            return []
        
        try:
            root = ET.fromstring(xml_content)
            matching_verses = []
            query_lower = query.lower()
            
            for book_elem in root.findall('.//book'):
                book_id = book_elem.get('id', '')
                book_name = book_elem.get('name', book_id)
                
                for chapter_elem in book_elem.findall('.//chapter'):
                    try:
                        chapter_num = int(chapter_elem.get('number', 0))
                        for verse_elem in chapter_elem.findall('verse'):
                            try:
                                verse_num = int(verse_elem.get('number', 0))
                                text = verse_elem.text or ''.join(verse_elem.itertext())
                                
                                if text and query_lower in text.lower():
                                    matching_verses.append({
                                        'book_id': book_id,
                                        'book': book_name,
                                        'chapter': chapter_num,
                                        'verse': verse_num,
                                        'text': text.strip()
                                    })
                                    
                                    if len(matching_verses) >= limit:
                                        return matching_verses
                            except ValueError:
                                continue
                    except ValueError:
                        continue
            
            return matching_verses
            
        except ET.ParseError:
            return []
    
    def get_books_for_translation(self, translation_id: str) -> List[Dict[str, str]]:
        """Get list of books available in a translation"""
        translation = self.get_translation_info(translation_id)
        if not translation:
            return []
        
        xml_content = self._get_xml_content(translation['file_path'])
        if not xml_content:
            return []
        
        try:
            root = ET.fromstring(xml_content)
            books = []
            
            for book_elem in root.findall('.//book'):
                book_id = book_elem.get('id', '')
                book_name = book_elem.get('name', book_id)
                
                if book_id and book_name:
                    books.append({
                        'id': book_id,
                        'name': book_name
                    })
            
            return books
            
        except ET.ParseError:
            return []