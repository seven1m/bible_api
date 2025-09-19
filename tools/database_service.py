"""
Database service for Bible XML importer.

This module provides database operations including connection management,
batch inserts, transactions, and error handling for Azure SQL Database.
"""

import logging
import time
from contextlib import contextmanager
from typing import List, Dict, Optional, Tuple, Any, Generator
from dataclasses import dataclass
import pyodbc

from .config import DatabaseConfig


logger = logging.getLogger(__name__)


@dataclass
class TranslationData:
    """Data structure for translation information."""
    identifier: str
    name: str
    language_code: str
    license: Optional[str] = None


@dataclass
class BookData:
    """Data structure for book information."""
    code: str
    name: str
    testament: Optional[str] = None


@dataclass
class VerseData:
    """Data structure for verse information."""
    translation_id: int
    book_id: int
    chapter_number: int
    verse_number: int
    text: str
    book_code: Optional[str] = None  # Added for mapping purposes


class DatabaseService:
    """Service for database operations with connection pooling and batch processing."""
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize the database service.
        
        Args:
            config: Database configuration settings
        """
        self.config = config
        self._connection_string = config.get_connection_string()
        self._setup_connection_pool()
    
    def _setup_connection_pool(self) -> None:
        """Set up the connection pool parameters."""
        # pyodbc doesn't have built-in connection pooling, but we can implement
        # basic connection management with retry logic
        logger.info(f"Setting up database connection to {self.config.server}")
        
        # Test the connection
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    @contextmanager
    def _get_connection(self) -> Generator[pyodbc.Connection, None, None]:
        """
        Get a database connection with retry logic.
        
        Yields:
            Database connection
        """
        connection = None
        for attempt in range(self.config.max_retries + 1):
            try:
                connection = pyodbc.connect(
                    self._connection_string,
                    timeout=self.config.connection_timeout
                )
                connection.timeout = self.config.command_timeout
                yield connection
                break
                
            except Exception as e:
                if connection:
                    connection.close()
                    connection = None
                
                if attempt == self.config.max_retries:
                    logger.error(f"Failed to connect to database after {self.config.max_retries + 1} attempts: {e}")
                    raise
                
                logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                
            finally:
                if connection:
                    connection.close()
    
    def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_or_create_translation(self, translation_data: TranslationData) -> int:
        """
        Get existing translation ID or create a new translation.
        
        Args:
            translation_data: Translation information
            
        Returns:
            Translation ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if translation exists
            cursor.execute(
                "SELECT TranslationId FROM dbo.Translation WHERE Identifier = ?",
                (translation_data.identifier,)
            )
            row = cursor.fetchone()
            
            if row:
                translation_id = row[0]
                logger.info(f"Found existing translation '{translation_data.identifier}' with ID {translation_id}")
                return translation_id
            
            # Create new translation
            cursor.execute("""
                INSERT INTO dbo.Translation (Identifier, Name, LanguageCode, License)
                VALUES (?, ?, ?, ?)
            """, (
                translation_data.identifier,
                translation_data.name,
                translation_data.language_code,
                translation_data.license
            ))
            
            # Get the new ID
            cursor.execute("SELECT SCOPE_IDENTITY()")
            translation_id = cursor.fetchone()[0]
            
            conn.commit()
            logger.info(f"Created new translation '{translation_data.identifier}' with ID {translation_id}")
            return translation_id
    
    def get_or_create_books(self, books_data: List[BookData]) -> Dict[str, int]:
        """
        Get existing book IDs or create new books.
        
        Args:
            books_data: List of book information
            
        Returns:
            Dictionary mapping book codes to book IDs
        """
        book_code_to_id = {}
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get existing books
            cursor.execute("SELECT Code, BookId FROM dbo.Book")
            existing_books = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Prepare new books for batch insert
            new_books = []
            for book_data in books_data:
                if book_data.code in existing_books:
                    book_code_to_id[book_data.code] = existing_books[book_data.code]
                else:
                    new_books.append((book_data.code, book_data.name, book_data.testament))
            
            # Batch insert new books
            if new_books:
                logger.info(f"Creating {len(new_books)} new books")
                cursor.executemany("""
                    INSERT INTO dbo.Book (Code, Name, Testament)
                    VALUES (?, ?, ?)
                """, new_books)
                
                # Get the new book IDs
                cursor.execute("SELECT Code, BookId FROM dbo.Book WHERE Code IN ({})".format(
                    ','.join('?' * len(new_books))
                ), [book[0] for book in new_books])
                
                for row in cursor.fetchall():
                    book_code_to_id[row[0]] = row[1]
                
                conn.commit()
                logger.info(f"Successfully created {len(new_books)} new books")
            
            return book_code_to_id
    
    def insert_verses_batch(self, verses_data: List[VerseData], progress_callback=None) -> Tuple[int, int]:
        """
        Insert verses in batches with progress tracking.
        
        Args:
            verses_data: List of verse data
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (inserted_count, skipped_count)
        """
        if not verses_data:
            return 0, 0
        
        total_verses = len(verses_data)
        inserted_count = 0
        skipped_count = 0
        
        logger.info(f"Starting batch insert of {total_verses} verses")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Process in batches
                for i in range(0, total_verses, self.config.batch_size):
                    batch = verses_data[i:i + self.config.batch_size]
                    batch_data = [
                        (v.translation_id, v.book_id, v.chapter_number, v.verse_number, v.text)
                        for v in batch
                    ]
                    
                    # Check for existing verses to avoid duplicates
                    if self.config.skip_existing:
                        existing_verses = self._get_existing_verses(
                            cursor, 
                            batch[0].translation_id,
                            [(v.book_id, v.chapter_number, v.verse_number) for v in batch]
                        )
                        
                        # Filter out existing verses
                        filtered_batch = []
                        for j, verse_data in enumerate(batch_data):
                            verse_key = (verse_data[1], verse_data[2], verse_data[3])  # book_id, chapter, verse
                            if verse_key not in existing_verses:
                                filtered_batch.append(verse_data)
                            else:
                                skipped_count += 1
                        
                        batch_data = filtered_batch
                    
                    # Insert the batch
                    if batch_data:
                        cursor.executemany("""
                            INSERT INTO dbo.Verse (TranslationId, BookId, ChapterNumber, VerseNumber, Text)
                            VALUES (?, ?, ?, ?, ?)
                        """, batch_data)
                        
                        inserted_count += len(batch_data)
                    
                    # Update FTKey values for the inserted verses
                    if batch_data:
                        cursor.execute("""
                            UPDATE dbo.Verse 
                            SET FTKey = VerseId 
                            WHERE FTKey = 0 OR FTKey IS NULL
                        """)
                    
                    # Progress callback
                    if progress_callback:
                        progress_callback(min(i + self.config.batch_size, total_verses), total_verses)
                    
                    # Log progress
                    if i % (self.config.batch_size * 10) == 0:
                        logger.info(f"Processed {min(i + self.config.batch_size, total_verses)}/{total_verses} verses")
                
                conn.commit()
                logger.info(f"Batch insert completed: {inserted_count} inserted, {skipped_count} skipped")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Error during batch insert: {e}")
                raise
        
        return inserted_count, skipped_count
    
    def _get_existing_verses(self, cursor: pyodbc.Cursor, translation_id: int, 
                           verse_keys: List[Tuple[int, int, int]]) -> set:
        """
        Get existing verses for duplicate checking.
        
        Args:
            cursor: Database cursor
            translation_id: Translation ID
            verse_keys: List of (book_id, chapter_number, verse_number) tuples
            
        Returns:
            Set of existing verse keys
        """
        if not verse_keys:
            return set()
        
        # Create a temporary table for the keys
        placeholders = ','.join(['(?,?,?)'] * len(verse_keys))
        flat_keys = [item for sublist in verse_keys for item in sublist]
        
        query = f"""
            SELECT BookId, ChapterNumber, VerseNumber
            FROM dbo.Verse
            WHERE TranslationId = ? AND (BookId, ChapterNumber, VerseNumber) IN 
            (VALUES {placeholders})
        """
        
        cursor.execute(query, [translation_id] + flat_keys)
        return {(row[0], row[1], row[2]) for row in cursor.fetchall()}
    
    def get_translation_statistics(self, translation_id: int) -> Dict[str, Any]:
        """
        Get statistics for a translation.
        
        Args:
            translation_id: Translation ID
            
        Returns:
            Dictionary with translation statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get basic translation info
            cursor.execute("""
                SELECT Identifier, Name, LanguageCode, CreatedAt
                FROM dbo.Translation
                WHERE TranslationId = ?
            """, (translation_id,))
            
            translation_info = cursor.fetchone()
            if not translation_info:
                raise ValueError(f"Translation with ID {translation_id} not found")
            
            # Get verse count
            cursor.execute("""
                SELECT COUNT(*) as VerseCount
                FROM dbo.Verse
                WHERE TranslationId = ?
            """, (translation_id,))
            verse_count = cursor.fetchone()[0]
            
            # Get book count
            cursor.execute("""
                SELECT COUNT(DISTINCT BookId) as BookCount
                FROM dbo.Verse
                WHERE TranslationId = ?
            """, (translation_id,))
            book_count = cursor.fetchone()[0]
            
            # Get chapter count
            cursor.execute("""
                SELECT COUNT(DISTINCT CONCAT(BookId, '-', ChapterNumber)) as ChapterCount
                FROM dbo.Verse
                WHERE TranslationId = ?
            """, (translation_id,))
            chapter_count = cursor.fetchone()[0]
            
            return {
                "translation_id": translation_id,
                "identifier": translation_info[0],
                "name": translation_info[1],
                "language_code": translation_info[2],
                "created_at": translation_info[3],
                "verse_count": verse_count,
                "book_count": book_count,
                "chapter_count": chapter_count
            }
    
    def cleanup_incomplete_translation(self, translation_id: int) -> None:
        """
        Clean up an incomplete translation (remove all verses and the translation record).
        
        Args:
            translation_id: Translation ID to clean up
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Delete verses first (due to foreign key constraint)
                cursor.execute("DELETE FROM dbo.Verse WHERE TranslationId = ?", (translation_id,))
                verses_deleted = cursor.rowcount
                
                # Delete translation
                cursor.execute("DELETE FROM dbo.Translation WHERE TranslationId = ?", (translation_id,))
                translation_deleted = cursor.rowcount
                
                conn.commit()
                logger.info(f"Cleaned up translation {translation_id}: {verses_deleted} verses, {translation_deleted} translation record")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Error cleaning up translation {translation_id}: {e}")
                raise