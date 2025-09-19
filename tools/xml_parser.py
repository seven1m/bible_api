"""
XML parsing service for Bible XML importer.

This module provides functionality to parse Bible XML files and extract
translation, book, and verse data with support for both streaming and
in-memory parsing based on file size.
"""

import io
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Generator, Tuple, Any
from dataclasses import dataclass

from .config import ImporterConfig
from .database_service import TranslationData, BookData, VerseData


logger = logging.getLogger(__name__)


@dataclass
class ParsedBibleData:
    """Container for parsed Bible data."""
    translation: TranslationData
    books: List[BookData]
    verses: List[VerseData]
    statistics: Dict[str, Any]


class XMLParsingError(Exception):
    """Custom exception for XML parsing errors."""
    pass


class BibleXMLParser:
    """Parser for Bible XML files with support for different formats."""
    
    def __init__(self, config: ImporterConfig):
        """
        Initialize the XML parser.
        
        Args:
            config: Importer configuration settings
        """
        self.config = config
        self._book_code_map = self._create_book_code_map()
    
    def parse_bible_xml(self, xml_stream: io.BytesIO, file_size_mb: Optional[float] = None) -> ParsedBibleData:
        """
        Parse Bible XML from a stream.
        
        Args:
            xml_stream: XML data stream
            file_size_mb: Size of the file in MB for choosing parsing strategy
            
        Returns:
            Parsed Bible data
            
        Raises:
            XMLParsingError: If parsing fails
        """
        try:
            xml_stream.seek(0)
            
            # Choose parsing strategy based on file size
            if file_size_mb and file_size_mb > self.config.streaming_threshold_mb:
                logger.info(f"Using streaming parser for large file ({file_size_mb:.1f} MB)")
                return self._parse_streaming(xml_stream)
            else:
                logger.info(f"Using in-memory parser for file ({file_size_mb or 0:.1f} MB)")
                return self._parse_in_memory(xml_stream)
                
        except ET.ParseError as e:
            raise XMLParsingError(f"XML parsing error: {e}")
        except Exception as e:
            raise XMLParsingError(f"Unexpected error during XML parsing: {e}")
    
    def _parse_in_memory(self, xml_stream: io.BytesIO) -> ParsedBibleData:
        """
        Parse XML using in-memory strategy.
        
        Args:
            xml_stream: XML data stream
            
        Returns:
            Parsed Bible data
        """
        logger.info("Parsing XML in memory")
        
        try:
            tree = ET.parse(xml_stream)
            root = tree.getroot()
            
            # Detect XML format and parse accordingly
            if root.tag == 'osis':
                return self._parse_osis_format(root)
            elif root.tag in ['bible', 'Bible']:
                return self._parse_generic_bible_format(root)
            else:
                # Try to auto-detect format based on structure
                return self._parse_auto_detect_format(root)
                
        except Exception as e:
            raise XMLParsingError(f"Error parsing XML in memory: {e}")
    
    def _parse_streaming(self, xml_stream: io.BytesIO) -> ParsedBibleData:
        """
        Parse XML using streaming strategy for large files.
        
        Args:
            xml_stream: XML data stream
            
        Returns:
            Parsed Bible data
        """
        logger.info("Parsing XML with streaming")
        
        # For streaming, we'll use iterparse to process elements incrementally
        translation_data = None
        books_data = []
        verses_data = []
        books_found = set()
        verse_count = 0
        
        try:
            # Reset stream position
            xml_stream.seek(0)
            
            # Use iterparse for streaming
            context = ET.iterparse(xml_stream, events=('start', 'end'))
            context = iter(context)
            
            # Get root element
            event, root = next(context)
            
            current_book = None
            current_chapter = None
            
            for event, elem in context:
                if event == 'end':
                    # Process translation metadata
                    if elem.tag in ['header', 'work'] and translation_data is None:
                        translation_data = self._extract_translation_from_element(elem)
                    
                    # Process book elements
                    elif elem.tag in ['div', 'book'] and elem.get('type') in ['book', None]:
                        book_data = self._extract_book_from_element(elem)
                        if book_data and book_data.code not in books_found:
                            books_data.append(book_data)
                            books_found.add(book_data.code)
                        current_book = book_data
                    
                    # Process chapter elements
                    elif elem.tag in ['chapter', 'div'] and elem.get('type') == 'chapter':
                        current_chapter = self._extract_chapter_number(elem)
                    
                    # Process verse elements
                    elif elem.tag in ['verse', 'v']:
                        if current_book and current_chapter:
                            verse_data = self._extract_verse_from_element(elem, current_book.code, current_chapter)
                            if verse_data:
                                verses_data.append(verse_data)
                                verse_count += 1
                                
                                # Log progress for large files
                                if verse_count % 1000 == 0:
                                    logger.info(f"Parsed {verse_count} verses")
                    
                    # Clear processed elements to save memory
                    elem.clear()
                    
                    # Memory usage check
                    if len(verses_data) > self.config.memory_limit_mb * 1000:  # Rough estimate
                        logger.warning("Memory limit reached during streaming parse")
                        break
            
            # Fallback for translation data if not found in header
            if translation_data is None:
                translation_data = self._create_default_translation()
            
            statistics = {
                "total_verses": len(verses_data),
                "total_books": len(books_data),
                "parsing_method": "streaming"
            }
            
            logger.info(f"Streaming parse completed: {len(verses_data)} verses, {len(books_data)} books")
            
            return ParsedBibleData(
                translation=translation_data,
                books=books_data,
                verses=verses_data,
                statistics=statistics
            )
            
        except Exception as e:
            raise XMLParsingError(f"Error during streaming parse: {e}")
    
    def _parse_osis_format(self, root: ET.Element) -> ParsedBibleData:
        """
        Parse OSIS format XML.
        
        Args:
            root: Root XML element
            
        Returns:
            Parsed Bible data
        """
        logger.info("Parsing OSIS format XML")
        
        # Extract translation metadata from header
        translation_data = self._extract_osis_translation(root)
        
        # Extract books and verses
        books_data = []
        verses_data = []
        books_found = set()
        
        # Find all div elements with type="book"
        for book_div in root.findall(".//div[@type='book']"):
            book_data = self._extract_osis_book(book_div)
            if book_data and book_data.code not in books_found:
                books_data.append(book_data)
                books_found.add(book_data.code)
            
            # Extract verses from this book
            for chapter_div in book_div.findall(".//div[@type='chapter']"):
                chapter_num = self._extract_osis_chapter_number(chapter_div)
                
                if book_data:  # Ensure book_data is not None
                    for verse in chapter_div.findall(".//verse"):
                        verse_data = self._extract_osis_verse(verse, book_data.code, chapter_num)
                        if verse_data:
                            verses_data.append(verse_data)
        
        statistics = {
            "total_verses": len(verses_data),
            "total_books": len(books_data),
            "parsing_method": "osis_in_memory"
        }
        
        return ParsedBibleData(
            translation=translation_data,
            books=books_data,
            verses=verses_data,
            statistics=statistics
        )
    
    def _parse_generic_bible_format(self, root: ET.Element) -> ParsedBibleData:
        """
        Parse generic Bible XML format.
        
        Args:
            root: Root XML element
            
        Returns:
            Parsed Bible data
        """
        logger.info("Parsing generic Bible format XML")
        
        # Try to extract translation info from root attributes or child elements
        translation_data = self._extract_generic_translation(root)
        
        books_data = []
        verses_data = []
        books_found = set()
        
        # Look for book elements
        for book_elem in root.findall(".//book"):
            book_data = self._extract_generic_book(book_elem)
            if book_data and book_data.code not in books_found:
                books_data.append(book_data)
                books_found.add(book_data.code)
            
            # Extract chapters and verses
            for chapter_elem in book_elem.findall(".//chapter"):
                chapter_num = int(chapter_elem.get('number', chapter_elem.get('id', '1')))
                
                if book_data:  # Ensure book_data is not None
                    for verse_elem in chapter_elem.findall(".//verse"):
                        verse_data = self._extract_generic_verse(verse_elem, book_data.code, chapter_num)
                        if verse_data:
                            verses_data.append(verse_data)
        
        statistics = {
            "total_verses": len(verses_data),
            "total_books": len(books_data),
            "parsing_method": "generic_in_memory"
        }
        
        return ParsedBibleData(
            translation=translation_data,
            books=books_data,
            verses=verses_data,
            statistics=statistics
        )
    
    def _parse_auto_detect_format(self, root: ET.Element) -> ParsedBibleData:
        """
        Auto-detect and parse unknown XML format.
        
        Args:
            root: Root XML element
            
        Returns:
            Parsed Bible data
        """
        logger.info(f"Auto-detecting XML format for root tag '{root.tag}'")
        
        # Try different parsing strategies
        strategies = [
            self._parse_generic_bible_format,
            self._parse_osis_format
        ]
        
        for strategy in strategies:
            try:
                result = strategy(root)
                if result.verses:  # If we got verses, consider it successful
                    logger.info(f"Successfully parsed with {strategy.__name__}")
                    return result
            except Exception as e:
                logger.warning(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        # Fallback: create minimal data structure
        logger.warning("All parsing strategies failed, creating minimal structure")
        return ParsedBibleData(
            translation=self._create_default_translation(),
            books=[],
            verses=[],
            statistics={"total_verses": 0, "total_books": 0, "parsing_method": "fallback"}
        )
    
    def _extract_osis_translation(self, root: ET.Element) -> TranslationData:
        """Extract translation data from OSIS header."""
        header = root.find(".//header")
        if header is not None:
            work = header.find(".//work")
            if work is not None:
                identifier = work.get('osisWork', 'unknown')
                title_elem = work.find('.//title')
                name = title_elem.text if title_elem is not None else identifier
                
                # Try to extract language
                lang_elem = work.find('.//language')
                language_code = lang_elem.get('ident', 'en') if lang_elem is not None else 'en'
                
                # Try to extract license
                rights_elem = work.find('.//rights')
                license_text = rights_elem.text if rights_elem is not None else None
                
                return TranslationData(
                    identifier=identifier,
                    name=name or identifier,
                    language_code=language_code,
                    license=license_text
                )
        
        return self._create_default_translation()
    
    def _extract_osis_book(self, book_div: ET.Element) -> Optional[BookData]:
        """Extract book data from OSIS book div."""
        osis_id = book_div.get('osisID', '')
        if not osis_id:
            return None
        
        # Map OSIS book ID to standard book code
        book_code = self._map_osis_to_book_code(osis_id)
        book_name = self._get_book_name_from_code(book_code)
        testament = self._get_testament_from_code(book_code)
        
        return BookData(
            code=book_code,
            name=book_name,
            testament=testament
        )
    
    def _extract_osis_chapter_number(self, chapter_div: ET.Element) -> int:
        """Extract chapter number from OSIS chapter div."""
        osis_id = chapter_div.get('osisID', '')
        if '.' in osis_id:
            try:
                return int(osis_id.split('.')[-1])
            except ValueError:
                pass
        
        # Fallback to number attribute
        return int(chapter_div.get('n', '1'))
    
    def _extract_osis_verse(self, verse_elem: ET.Element, book_code: str, chapter_num: int) -> Optional[VerseData]:
        """Extract verse data from OSIS verse element."""
        osis_id = verse_elem.get('osisID', '')
        if not osis_id:
            return None
        
        # Extract verse number from osisID (e.g., "Gen.1.1" -> 1)
        try:
            verse_num = int(osis_id.split('.')[-1])
        except (ValueError, IndexError):
            verse_num = int(verse_elem.get('n', '1'))
        
        # Get verse text
        text = self._extract_text_content(verse_elem)
        if not text.strip():
            return None
        
        return VerseData(
            translation_id=0,  # Will be set later
            book_id=0,         # Will be set later
            chapter_number=chapter_num,
            verse_number=verse_num,
            text=text.strip(),
            book_code=book_code  # Include book code for mapping
        )
    
    def _extract_text_content(self, element: ET.Element) -> str:
        """Extract text content from an element, handling nested elements."""
        def get_text_recursive(elem):
            text = elem.text or ''
            for child in elem:
                text += get_text_recursive(child)
                text += child.tail or ''
            return text
        
        return get_text_recursive(element)
    
    def _create_default_translation(self) -> TranslationData:
        """Create a default translation data structure."""
        return TranslationData(
            identifier='imported_translation',
            name='Imported Bible Translation',
            language_code='en',
            license=None
        )
    
    def _create_book_code_map(self) -> Dict[str, str]:
        """Create mapping of various book identifiers to standard codes."""
        return {
            # OSIS book codes
            'Gen': 'GEN', 'Exod': 'EXO', 'Lev': 'LEV', 'Num': 'NUM', 'Deut': 'DEU',
            'Josh': 'JOS', 'Judg': 'JDG', 'Ruth': 'RUT', '1Sam': '1SA', '2Sam': '2SA',
            '1Kgs': '1KI', '2Kgs': '2KI', '1Chr': '1CH', '2Chr': '2CH', 'Ezra': 'EZR',
            'Neh': 'NEH', 'Esth': 'EST', 'Job': 'JOB', 'Ps': 'PSA', 'Prov': 'PRO',
            'Eccl': 'ECC', 'Song': 'SON', 'Isa': 'ISA', 'Jer': 'JER', 'Lam': 'LAM',
            'Ezek': 'EZE', 'Dan': 'DAN', 'Hos': 'HOS', 'Joel': 'JOE', 'Amos': 'AMO',
            'Obad': 'OBA', 'Jonah': 'JON', 'Mic': 'MIC', 'Nah': 'NAH', 'Hab': 'HAB',
            'Zeph': 'ZEP', 'Hag': 'HAG', 'Zech': 'ZEC', 'Mal': 'MAL',
            'Matt': 'MAT', 'Mark': 'MAR', 'Luke': 'LUK', 'John': 'JOH', 'Acts': 'ACT',
            'Rom': 'ROM', '1Cor': '1CO', '2Cor': '2CO', 'Gal': 'GAL', 'Eph': 'EPH',
            'Phil': 'PHI', 'Col': 'COL', '1Thess': '1TH', '2Thess': '2TH', '1Tim': '1TI',
            '2Tim': '2TI', 'Titus': 'TIT', 'Phlm': 'PHM', 'Heb': 'HEB', 'Jas': 'JAM',
            '1Pet': '1PE', '2Pet': '2PE', '1John': '1JO', '2John': '2JO', '3John': '3JO',
            'Jude': 'JUD', 'Rev': 'REV',
            
            # Common variations
            'Genesis': 'GEN', 'Exodus': 'EXO', 'Leviticus': 'LEV', 'Numbers': 'NUM',
            'Deuteronomy': 'DEU', 'Joshua': 'JOS', 'Judges': 'JDG', 'Ruth': 'RUT',
            'Samuel1': '1SA', 'Samuel2': '2SA', 'Kings1': '1KI', 'Kings2': '2KI',
            'Chronicles1': '1CH', 'Chronicles2': '2CH', 'Ezra': 'EZR', 'Nehemiah': 'NEH',
            'Esther': 'EST', 'Job': 'JOB', 'Psalms': 'PSA', 'Proverbs': 'PRO',
            'Ecclesiastes': 'ECC', 'SongofSongs': 'SON', 'Isaiah': 'ISA', 'Jeremiah': 'JER',
            'Lamentations': 'LAM', 'Ezekiel': 'EZE', 'Daniel': 'DAN', 'Hosea': 'HOS',
            'Joel': 'JOE', 'Amos': 'AMO', 'Obadiah': 'OBA', 'Jonah': 'JON', 'Micah': 'MIC',
            'Nahum': 'NAH', 'Habakkuk': 'HAB', 'Zephaniah': 'ZEP', 'Haggai': 'HAG',
            'Zechariah': 'ZEC', 'Malachi': 'MAL', 'Matthew': 'MAT', 'Mark': 'MAR',
            'Luke': 'LUK', 'John': 'JOH', 'Acts': 'ACT', 'Romans': 'ROM',
            'Corinthians1': '1CO', 'Corinthians2': '2CO', 'Galatians': 'GAL',
            'Ephesians': 'EPH', 'Philippians': 'PHI', 'Colossians': 'COL',
            'Thessalonians1': '1TH', 'Thessalonians2': '2TH', 'Timothy1': '1TI',
            'Timothy2': '2TI', 'Titus': 'TIT', 'Philemon': 'PHM', 'Hebrews': 'HEB',
            'James': 'JAM', 'Peter1': '1PE', 'Peter2': '2PE', 'John1': '1JO',
            'John2': '2JO', 'John3': '3JO', 'Jude': 'JUD', 'Revelation': 'REV'
        }
    
    def _map_osis_to_book_code(self, osis_id: str) -> str:
        """Map OSIS book ID to standard book code."""
        # Extract book part from osisID (e.g., "Gen.1.1" -> "Gen")
        book_part = osis_id.split('.')[0]
        return self._book_code_map.get(book_part, book_part.upper()[:3])
    
    def _get_book_name_from_code(self, book_code: str) -> str:
        """Get full book name from book code."""
        book_names = {
            'GEN': 'Genesis', 'EXO': 'Exodus', 'LEV': 'Leviticus', 'NUM': 'Numbers',
            'DEU': 'Deuteronomy', 'JOS': 'Joshua', 'JDG': 'Judges', 'RUT': 'Ruth',
            '1SA': '1 Samuel', '2SA': '2 Samuel', '1KI': '1 Kings', '2KI': '2 Kings',
            '1CH': '1 Chronicles', '2CH': '2 Chronicles', 'EZR': 'Ezra', 'NEH': 'Nehemiah',
            'EST': 'Esther', 'JOB': 'Job', 'PSA': 'Psalms', 'PRO': 'Proverbs',
            'ECC': 'Ecclesiastes', 'SON': 'Song of Songs', 'ISA': 'Isaiah', 'JER': 'Jeremiah',
            'LAM': 'Lamentations', 'EZE': 'Ezekiel', 'DAN': 'Daniel', 'HOS': 'Hosea',
            'JOE': 'Joel', 'AMO': 'Amos', 'OBA': 'Obadiah', 'JON': 'Jonah', 'MIC': 'Micah',
            'NAH': 'Nahum', 'HAB': 'Habakkuk', 'ZEP': 'Zephaniah', 'HAG': 'Haggai',
            'ZEC': 'Zechariah', 'MAL': 'Malachi', 'MAT': 'Matthew', 'MAR': 'Mark',
            'LUK': 'Luke', 'JOH': 'John', 'ACT': 'Acts', 'ROM': 'Romans',
            '1CO': '1 Corinthians', '2CO': '2 Corinthians', 'GAL': 'Galatians',
            'EPH': 'Ephesians', 'PHI': 'Philippians', 'COL': 'Colossians',
            '1TH': '1 Thessalonians', '2TH': '2 Thessalonians', '1TI': '1 Timothy',
            '2TI': '2 Timothy', 'TIT': 'Titus', 'PHM': 'Philemon', 'HEB': 'Hebrews',
            'JAM': 'James', '1PE': '1 Peter', '2PE': '2 Peter', '1JO': '1 John',
            '2JO': '2 John', '3JO': '3 John', 'JUD': 'Jude', 'REV': 'Revelation'
        }
        return book_names.get(book_code, book_code)
    
    def _get_testament_from_code(self, book_code: str) -> str:
        """Get testament (OT/NT) from book code."""
        ot_books = {
            'GEN', 'EXO', 'LEV', 'NUM', 'DEU', 'JOS', 'JDG', 'RUT', '1SA', '2SA',
            '1KI', '2KI', '1CH', '2CH', 'EZR', 'NEH', 'EST', 'JOB', 'PSA', 'PRO',
            'ECC', 'SON', 'ISA', 'JER', 'LAM', 'EZE', 'DAN', 'HOS', 'JOE', 'AMO',
            'OBA', 'JON', 'MIC', 'NAH', 'HAB', 'ZEP', 'HAG', 'ZEC', 'MAL'
        }
        return 'OT' if book_code in ot_books else 'NT'
    
    # Stub methods for generic format parsing (can be expanded)
    def _extract_generic_translation(self, root: ET.Element) -> TranslationData:
        """Extract translation from generic format."""
        return self._create_default_translation()
    
    def _extract_generic_book(self, book_elem: ET.Element) -> Optional[BookData]:
        """Extract book from generic format."""
        return None
    
    def _extract_generic_verse(self, verse_elem: ET.Element, book_code: str, chapter_num: int) -> Optional[VerseData]:
        """Extract verse from generic format."""
        return None
    
    def _extract_translation_from_element(self, elem: ET.Element) -> Optional[TranslationData]:
        """Extract translation data from streaming element."""
        return None
    
    def _extract_book_from_element(self, elem: ET.Element) -> Optional[BookData]:
        """Extract book data from streaming element.""" 
        return None
    
    def _extract_chapter_number(self, elem: ET.Element) -> Optional[int]:
        """Extract chapter number from streaming element."""
        return None
    
    def _extract_verse_from_element(self, elem: ET.Element, book_code: str, chapter_num: int) -> Optional[VerseData]:
        """Extract verse data from streaming element."""
        return None