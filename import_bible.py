#!/usr/bin/env python3

import os
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, Any, Optional
import xml.etree.ElementTree as ET
from io import StringIO

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# Azure Blob Storage imports
try:
    from azure.storage.blob import BlobServiceClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

# Load environment variables
load_dotenv()

# Database models (same as main.py)
Base = declarative_base()

class Translation(Base):
    __tablename__ = 'translations'
    
    id = Column(Integer, primary_key=True)
    identifier = Column(String(255))
    name = Column(String(255))
    language = Column(String(255))
    language_code = Column(String(255))
    license = Column(String(255))

class Verse(Base):
    __tablename__ = 'verses'
    
    id = Column(Integer, primary_key=True)
    book_num = Column(Integer)
    book_id = Column(String(255))
    book = Column(String(255))
    chapter = Column(Integer)
    verse = Column(Integer)
    text = Column(Text)
    translation_id = Column(Integer)

class BibleImporter:
    """Bible data importer for OSIS XML files"""
    
    def __init__(self, database_url: str):
        # Add charset to URL instead of using deprecated encoding parameter
        if 'charset' not in database_url:
            connector = '&' if '?' in database_url else '?'
            database_url += f'{connector}charset=utf8mb4'
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Initialize Azure Blob Storage client if configured
        self.blob_service_client = None
        self.container_name = None
        self._init_azure_storage()
        
    def _init_azure_storage(self):
        """Initialize Azure Blob Storage client if configured"""
        if not AZURE_AVAILABLE:
            return
            
        # Check for Azure configuration
        azure_connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        azure_account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
        azure_account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
        self.container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'bibles')
        
        try:
            if azure_connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
                print(f"  Azure Blob Storage configured with connection string (container: {self.container_name})")
            elif azure_account_name and azure_account_key:
                account_url = f"https://{azure_account_name}.blob.core.windows.net"
                self.blob_service_client = BlobServiceClient(account_url=account_url, credential=azure_account_key)
                print(f"  Azure Blob Storage configured with account name and key (container: {self.container_name})")
            else:
                print("  Azure Blob Storage not configured - will use local files")
        except Exception as e:
            print(f"  Warning: Failed to initialize Azure Blob Storage: {e}")
            self.blob_service_client = None
        
    def create_tables(self, drop_first: bool = False):
        """Create database tables"""
        if drop_first:
            Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
    
    def _read_file_content(self, file_path: str) -> str:
        """Read file content from Azure Blob Storage or local file system"""
        if self.blob_service_client and self.container_name:
            try:
                # Extract blob name from file path (remove directory structure)
                blob_name = os.path.basename(file_path)
                blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_name)
                
                # Download blob content as text
                content = blob_client.download_blob().readall().decode('utf-8')
                print(f"    read from Azure Blob Storage: {blob_name}")
                return content
            except Exception as e:
                print(f"    Warning: Failed to read {file_path} from Azure Blob Storage: {e}")
                print(f"    Falling back to local file...")
        
        # Fallback to local file reading
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"    read from local file: {file_path}")
                return content
        except Exception as e:
            raise Exception(f"Failed to read file {file_path}: {e}")
    
    def list_bible_files(self, bibles_path: str) -> list:
        """List Bible XML files from Azure Blob Storage or local directory"""
        files = []
        
        if self.blob_service_client and self.container_name:
            try:
                # List blobs in the container
                blob_list = self.blob_service_client.get_container_client(self.container_name).list_blobs()
                for blob in blob_list:
                    if blob.name.endswith('.xml'):
                        # Create a pseudo file path for compatibility with existing code
                        file_path = os.path.join(bibles_path, blob.name)
                        files.append((file_path, blob.name))
                print(f"  Found {len(files)} XML files in Azure Blob Storage container '{self.container_name}'")
                return files
            except Exception as e:
                print(f"  Warning: Failed to list blobs from Azure Blob Storage: {e}")
                print(f"  Falling back to local files...")
        
        # Fallback to local file listing
        try:
            for file_path in Path(bibles_path).glob('*.xml'):
                files.append((str(file_path), file_path.name))
            print(f"  Found {len(files)} XML files in local directory '{bibles_path}'")
            return files
        except Exception as e:
            print(f"  Error listing files in {bibles_path}: {e}")
            return []
    
    def parse_osis_file(self, file_path: str) -> Dict[str, Any]:
        """Parse OSIS XML file and extract verses"""
        print(f"  parsing {file_path}...")
        
        try:
            # Read file content from Azure Blob Storage or local file
            content = self._read_file_content(file_path)
            root = ET.fromstring(content)
        except ET.ParseError as e:
            print(f"  Error parsing XML: {e}")
            return {}
        
        # OSIS namespace
        ns = {'osis': 'http://www.bibletechnologies.net/2003/OSIS/namespace'}
        
        verses = []
        
        # Try modern OSIS format first (with sID/eID pattern)
        verse_starts = root.findall('.//osis:verse[@sID]', ns)
        if verse_starts:
            print(f"    found {len(verse_starts)} verses using OSIS sID/eID pattern")
            for verse_elem in verse_starts:
                verse_data = self.extract_osis_verse_data(verse_elem, root, ns)
                if verse_data:
                    verses.append(verse_data)
        else:
            # Fallback to older OSIS format or other verse patterns
            all_verses = root.findall('.//osis:verse', ns)
            print(f"    found {len(all_verses)} verse elements, trying legacy format")
            for verse_elem in all_verses:
                verse_data = self.extract_verse_data(verse_elem, ns)
                if verse_data:
                    verses.append(verse_data)
        
        return {'verses': verses}
    
    def extract_osis_verse_data(self, verse_start_elem, root, ns: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Extract verse data from OSIS verse start element"""
        # Get verse ID (e.g., "Gen.1.1")
        osisID = verse_start_elem.get('osisID')
        if not osisID:
            return None
        
        # Parse the verse reference
        parts = osisID.split('.')
        if len(parts) < 3:
            return None
        
        book_id = parts[0]
        try:
            chapter = int(parts[1])
            verse_num = int(parts[2])
        except ValueError:
            return None
        
        # Find the corresponding end element
        sID = verse_start_elem.get('sID')
        eID = sID.replace('sID', 'eID') if sID else None
        
        # Extract verse text between start and end elements
        text = self.extract_text_between_verse_markers(verse_start_elem, eID, root)
        if not text:
            return None
        
        # Map OSIS book IDs to standard ones (simplified mapping)
        book_mapping = {
            'Gen': 'GEN', 'Exod': 'EXO', 'Lev': 'LEV', 'Num': 'NUM', 'Deut': 'DEU',
            'Josh': 'JOS', 'Judg': 'JDG', 'Ruth': 'RUT', '1Sam': '1SA', '2Sam': '2SA',
            '1Kgs': '1KI', '2Kgs': '2KI', '1Chr': '1CH', '2Chr': '2CH', 'Ezra': 'EZR',
            'Neh': 'NEH', 'Esth': 'EST', 'Job': 'JOB', 'Ps': 'PSA', 'Prov': 'PRO',
            'Eccl': 'ECC', 'Song': 'SNG', 'Isa': 'ISA', 'Jer': 'JER', 'Lam': 'LAM',
            'Ezek': 'EZK', 'Dan': 'DAN', 'Hos': 'HOS', 'Joel': 'JOL', 'Amos': 'AMO',
            'Obad': 'OBA', 'Jonah': 'JON', 'Mic': 'MIC', 'Nah': 'NAM', 'Hab': 'HAB',
            'Zeph': 'ZEP', 'Hag': 'HAG', 'Zech': 'ZEC', 'Mal': 'MAL',
            'Matt': 'MAT', 'Mark': 'MRK', 'Luke': 'LUK', 'John': 'JHN', 'Acts': 'ACT',
            'Rom': 'ROM', '1Cor': '1CO', '2Cor': '2CO', 'Gal': 'GAL', 'Eph': 'EPH',
            'Phil': 'PHP', 'Col': 'COL', '1Thess': '1TH', '2Thess': '2TH', '1Tim': '1TI',
            '2Tim': '2TI', 'Titus': 'TIT', 'Phlm': 'PHM', 'Heb': 'HEB', 'Jas': 'JAS',
            '1Pet': '1PE', '2Pet': '2PE', '1John': '1JN', '2John': '2JN', '3John': '3JN',
            'Jude': 'JUD', 'Rev': 'REV'
        }
        
        standard_book_id = book_mapping.get(book_id, book_id.upper())
        
        # Get book name (simplified)
        book_names = {
            'GEN': 'Genesis', 'EXO': 'Exodus', 'LEV': 'Leviticus', 'NUM': 'Numbers', 'DEU': 'Deuteronomy',
            'JOS': 'Joshua', 'JDG': 'Judges', 'RUT': 'Ruth', '1SA': '1 Samuel', '2SA': '2 Samuel',
            '1KI': '1 Kings', '2KI': '2 Kings', '1CH': '1 Chronicles', '2CH': '2 Chronicles', 'EZR': 'Ezra',
            'NEH': 'Nehemiah', 'EST': 'Esther', 'JOB': 'Job', 'PSA': 'Psalms', 'PRO': 'Proverbs',
            'ECC': 'Ecclesiastes', 'SNG': 'Song of Solomon', 'ISA': 'Isaiah', 'JER': 'Jeremiah', 'LAM': 'Lamentations',
            'EZK': 'Ezekiel', 'DAN': 'Daniel', 'HOS': 'Hosea', 'JOL': 'Joel', 'AMO': 'Amos',
            'OBA': 'Obadiah', 'JON': 'Jonah', 'MIC': 'Micah', 'NAM': 'Nahum', 'HAB': 'Habakkuk',
            'ZEP': 'Zephaniah', 'HAG': 'Haggai', 'ZEC': 'Zechariah', 'MAL': 'Malachi',
            'MAT': 'Matthew', 'MRK': 'Mark', 'LUK': 'Luke', 'JHN': 'John', 'ACT': 'Acts',
            'ROM': 'Romans', '1CO': '1 Corinthians', '2CO': '2 Corinthians', 'GAL': 'Galatians', 'EPH': 'Ephesians',
            'PHP': 'Philippians', 'COL': 'Colossians', '1TH': '1 Thessalonians', '2TH': '2 Thessalonians', '1TI': '1 Timothy',
            '2TI': '2 Timothy', 'TIT': 'Titus', 'PHM': 'Philemon', 'HEB': 'Hebrews', 'JAS': 'James',
            '1PE': '1 Peter', '2PE': '2 Peter', '1JN': '1 John', '2JN': '2 John', '3JN': '3 John',
            'JUD': 'Jude', 'REV': 'Revelation'
        }
        
        book_name = book_names.get(standard_book_id, standard_book_id)
        
        # Get book number (simplified order)
        protestant_books = [
            'GEN', 'EXO', 'LEV', 'NUM', 'DEU', 'JOS', 'JDG', 'RUT', '1SA', '2SA', '1KI', '2KI',
            '1CH', '2CH', 'EZR', 'NEH', 'EST', 'JOB', 'PSA', 'PRO', 'ECC', 'SNG', 'ISA', 'JER',
            'LAM', 'EZK', 'DAN', 'HOS', 'JOL', 'AMO', 'OBA', 'JON', 'MIC', 'NAM', 'HAB', 'ZEP',
            'HAG', 'ZEC', 'MAL', 'MAT', 'MRK', 'LUK', 'JHN', 'ACT', 'ROM', '1CO', '2CO', 'GAL',
            'EPH', 'PHP', 'COL', '1TH', '2TH', '1TI', '2TI', 'TIT', 'PHM', 'HEB', 'JAS', '1PE',
            '2PE', '1JN', '2JN', '3JN', 'JUD', 'REV'
        ]
        
        try:
            book_num = protestant_books.index(standard_book_id) + 1
        except ValueError:
            book_num = 999  # Unknown book
        
        return {
            'book_num': book_num,
            'book_id': standard_book_id,
            'book': book_name,
            'chapter': chapter,
            'verse': verse_num,
            'text': text.strip()
        }
    
    def extract_text_between_verse_markers(self, start_elem, eID: str, root) -> str:
        """Extract text between verse start and end markers in OSIS format - simplified approach"""
        if not eID:
            return ""
        
        # Simple approach: extract the tail text from the start element
        # This works for most OSIS files where the verse text immediately follows the start tag
        if start_elem.tail:
            # Clean up the text by removing extra whitespace and unwanted characters
            text = start_elem.tail.strip()
            # Remove verse end markers that might be embedded in the text
            text = text.replace('<verse', '').replace('/>', '')
            text = ' '.join(text.split())  # Normalize whitespace
            return text
        
        return ""
    
    def extract_verse_data(self, verse_elem, ns: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Extract verse data from OSIS verse element"""
        # Get verse ID (e.g., "Gen.1.1")
        osisID = verse_elem.get('osisID')
        if not osisID:
            return None
        
        # Parse the verse reference
        parts = osisID.split('.')
        if len(parts) < 3:
            return None
        
        book_id = parts[0].upper()
        try:
            chapter = int(parts[1])
            verse_num = int(parts[2])
        except ValueError:
            return None
        
        # Get verse text
        text = ''.join(verse_elem.itertext()).strip()
        if not text:
            return None
        
        # Map OSIS book IDs to standard ones (simplified mapping)
        book_mapping = {
            'Gen': 'GEN', 'Exod': 'EXO', 'Lev': 'LEV', 'Num': 'NUM', 'Deut': 'DEU',
            'Josh': 'JOS', 'Judg': 'JDG', 'Ruth': 'RUT', '1Sam': '1SA', '2Sam': '2SA',
            '1Kgs': '1KI', '2Kgs': '2KI', '1Chr': '1CH', '2Chr': '2CH', 'Ezra': 'EZR',
            'Neh': 'NEH', 'Esth': 'EST', 'Job': 'JOB', 'Ps': 'PSA', 'Prov': 'PRO',
            'Eccl': 'ECC', 'Song': 'SNG', 'Isa': 'ISA', 'Jer': 'JER', 'Lam': 'LAM',
            'Ezek': 'EZK', 'Dan': 'DAN', 'Hos': 'HOS', 'Joel': 'JOL', 'Amos': 'AMO',
            'Obad': 'OBA', 'Jonah': 'JON', 'Mic': 'MIC', 'Nah': 'NAM', 'Hab': 'HAB',
            'Zeph': 'ZEP', 'Hag': 'HAG', 'Zech': 'ZEC', 'Mal': 'MAL',
            'Matt': 'MAT', 'Mark': 'MRK', 'Luke': 'LUK', 'John': 'JHN', 'Acts': 'ACT',
            'Rom': 'ROM', '1Cor': '1CO', '2Cor': '2CO', 'Gal': 'GAL', 'Eph': 'EPH',
            'Phil': 'PHP', 'Col': 'COL', '1Thess': '1TH', '2Thess': '2TH', '1Tim': '1TI',
            '2Tim': '2TI', 'Titus': 'TIT', 'Phlm': 'PHM', 'Heb': 'HEB', 'Jas': 'JAS',
            '1Pet': '1PE', '2Pet': '2PE', '1John': '1JN', '2John': '2JN', '3John': '3JN',
            'Jude': 'JUD', 'Rev': 'REV'
        }
        
        standard_book_id = book_mapping.get(book_id, book_id)
        
        # Get book name (simplified)
        book_names = {
            'GEN': 'Genesis', 'EXO': 'Exodus', 'LEV': 'Leviticus', 'NUM': 'Numbers', 'DEU': 'Deuteronomy',
            'JOS': 'Joshua', 'JDG': 'Judges', 'RUT': 'Ruth', '1SA': '1 Samuel', '2SA': '2 Samuel',
            '1KI': '1 Kings', '2KI': '2 Kings', '1CH': '1 Chronicles', '2CH': '2 Chronicles', 'EZR': 'Ezra',
            'NEH': 'Nehemiah', 'EST': 'Esther', 'JOB': 'Job', 'PSA': 'Psalms', 'PRO': 'Proverbs',
            'ECC': 'Ecclesiastes', 'SNG': 'Song of Solomon', 'ISA': 'Isaiah', 'JER': 'Jeremiah', 'LAM': 'Lamentations',
            'EZK': 'Ezekiel', 'DAN': 'Daniel', 'HOS': 'Hosea', 'JOL': 'Joel', 'AMO': 'Amos',
            'OBA': 'Obadiah', 'JON': 'Jonah', 'MIC': 'Micah', 'NAM': 'Nahum', 'HAB': 'Habakkuk',
            'ZEP': 'Zephaniah', 'HAG': 'Haggai', 'ZEC': 'Zechariah', 'MAL': 'Malachi',
            'MAT': 'Matthew', 'MRK': 'Mark', 'LUK': 'Luke', 'JHN': 'John', 'ACT': 'Acts',
            'ROM': 'Romans', '1CO': '1 Corinthians', '2CO': '2 Corinthians', 'GAL': 'Galatians', 'EPH': 'Ephesians',
            'PHP': 'Philippians', 'COL': 'Colossians', '1TH': '1 Thessalonians', '2TH': '2 Thessalonians', '1TI': '1 Timothy',
            '2TI': '2 Timothy', 'TIT': 'Titus', 'PHM': 'Philemon', 'HEB': 'Hebrews', 'JAS': 'James',
            '1PE': '1 Peter', '2PE': '2 Peter', '1JN': '1 John', '2JN': '2 John', '3JN': '3 John',
            'JUD': 'Jude', 'REV': 'Revelation'
        }
        
        book_name = book_names.get(standard_book_id, standard_book_id)
        
        # Get book number (simplified order)
        protestant_books = [
            'GEN', 'EXO', 'LEV', 'NUM', 'DEU', 'JOS', 'JDG', 'RUT', '1SA', '2SA', '1KI', '2KI',
            '1CH', '2CH', 'EZR', 'NEH', 'EST', 'JOB', 'PSA', 'PRO', 'ECC', 'SNG', 'ISA', 'JER',
            'LAM', 'EZK', 'DAN', 'HOS', 'JOL', 'AMO', 'OBA', 'JON', 'MIC', 'NAM', 'HAB', 'ZEP',
            'HAG', 'ZEC', 'MAL', 'MAT', 'MRK', 'LUK', 'JHN', 'ACT', 'ROM', '1CO', '2CO', 'GAL',
            'EPH', 'PHP', 'COL', '1TH', '2TH', '1TI', '2TI', 'TIT', 'PHM', 'HEB', 'JAS', '1PE',
            '2PE', '1JN', '2JN', '3JN', 'JUD', 'REV'
        ]
        
        try:
            book_num = protestant_books.index(standard_book_id) + 1
        except ValueError:
            book_num = 999  # Unknown book
        
        return {
            'book_num': book_num,
            'book_id': standard_book_id,
            'book': book_name,
            'chapter': chapter,
            'verse': verse_num,
            'text': text
        }
    
    def import_translation(self, file_path: str, translation_data: Dict[str, str], overwrite: bool = False):
        """Import a Bible translation"""
        print(f"Importing {file_path}")
        
        db = self.SessionLocal()
        try:
            # Check if translation already exists
            existing = db.query(Translation).filter(Translation.identifier == translation_data['identifier']).first()
            if existing:
                if overwrite:
                    # Delete existing verses and translation
                    db.query(Verse).filter(Verse.translation_id == existing.id).delete()
                    db.query(Translation).filter(Translation.id == existing.id).delete()
                    db.commit()
                else:
                    print("  skipping existing translation (use --overwrite)")
                    return
            
            # Create translation record
            translation = Translation(**translation_data)
            db.add(translation)
            db.flush()  # Get the ID
            translation_id = translation.id
            
            # Parse and import verses
            bible_data = self.parse_osis_file(file_path)
            
            if not bible_data.get('verses'):
                print("  No verses found in file")
                return
            
            print(f"  importing {len(bible_data['verses'])} verses...")
            
            for verse_data in bible_data['verses']:
                verse_data['translation_id'] = translation_id
                verse = Verse(**verse_data)
                db.add(verse)
                
                # Progress indicator
                if verse.chapter == 1 and verse.verse == 1:
                    print(f"  {translation_data['identifier']} - {verse.book} {verse.chapter}:{verse.verse}")
            
            db.commit()
            print("  done")
            
        except Exception as e:
            db.rollback()
            print(f"  Error importing {file_path}: {e}")
            raise
        finally:
            db.close()

def parse_readme_table(readme_path: str) -> list:
    """Parse translation info from README.md table"""
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"README.md not found at {readme_path}")
        return []
    
    # Find table lines
    lines = content.split('\n')
    table_lines = [line for line in lines if line.strip().startswith('|')]
    
    if len(table_lines) < 2:
        print("No table found in README.md")
        return []
    
    # Parse header
    header_line = table_lines[0]
    headers = [h.strip().lower() for h in header_line.split('|')[1:-1]]  # Remove empty first/last
    
    # Skip separator line
    data_lines = table_lines[2:]
    
    translations = []
    for line in data_lines:
        cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty first/last
        if len(cells) >= len(headers):
            translation = {}
            for i, header in enumerate(headers):
                if i < len(cells):
                    translation[header] = cells[i]
            translations.append(translation)
    
    return translations

def main():
    parser = argparse.ArgumentParser(description='Import Bible translations into database')
    parser.add_argument('-t', '--translation', help='Only import a single translation (e.g. eng-ylt.osis.xml)')
    parser.add_argument('--bibles-path', default='./bibles', help='Path to bibles directory (used for local files and README.md)')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing data')
    parser.add_argument('--drop-tables', action='store_true', help='Drop all tables first')
    
    args = parser.parse_args()
    
    # Check database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('Must set the DATABASE_URL environment variable (probably in .env)')
        sys.exit(1)
    
    # Convert mysql:// to mysql+pymysql://
    database_url = database_url.replace('mysql://', 'mysql+pymysql://')
    
    # Initialize importer
    importer = BibleImporter(database_url)
    
    # Create tables
    importer.create_tables(drop_first=args.drop_tables)
    
    # Parse README for translation info
    readme_path = os.path.join(args.bibles_path, 'README.md')
    translations = parse_readme_table(readme_path)
    
    if not translations:
        print("No translations found in README.md")
        sys.exit(1)
    
    # Get list of Bible files
    bible_files = importer.list_bible_files(args.bibles_path)
    if not bible_files:
        print("No XML files found")
        sys.exit(1)
    
    # Create lookup map for files
    file_map = {filename: file_path for file_path, filename in bible_files}
    
    # Import each translation
    for translation_info in translations:
        filename = translation_info.get('filename')
        if not filename:
            continue
            
        # Skip if specific translation requested and this isn't it
        if args.translation and filename != args.translation:
            continue
        
        if filename not in file_map:
            print(f"File not found: {filename}")
            continue
        
        file_path = file_map[filename]
        
        # Parse translation metadata
        lang_code_and_id = filename.split('.')[0]
        lang_parts = lang_code_and_id.split('-')
        
        if len(lang_parts) == 3:
            language_code = lang_parts[0]
            identifier = translation_info.get('abbrev', '').lower()
            if not identifier:
                print(f"Bad abbrev for {filename}")
                continue
        elif len(lang_parts) == 2:
            language_code, identifier = lang_parts
        else:
            print(f"Error with language and id for {filename}: {lang_parts}")
            continue
        
        # Handle special cases
        if language_code == 'chi':
            language_code = 'zh-tw'
        
        # Build translation data
        translation_data = {
            'identifier': identifier.lower(),
            'name': translation_info.get('version', ''),
            'language': translation_info.get('language', ''),
            'language_code': language_code,
            'license': translation_info.get('license', '')
        }
        
        # Skip if missing required fields
        if not all([translation_data['identifier'], translation_data['name']]):
            print(f"Missing required fields for {filename}")
            continue
        
        # Import the translation
        try:
            importer.import_translation(file_path, translation_data, args.overwrite)
        except Exception as e:
            print(f"Failed to import {filename}: {e}")
            continue

if __name__ == '__main__':
    main()