#!/usr/bin/env python3
"""
Bible XML Importer - Azure Blob Storage to Azure SQL Database

This script imports Bible XML files from Azure Blob Storage into Azure SQL Database
with comprehensive error handling, progress tracking, and performance optimization.

Usage:
    python bible_importer.py <xml_filename>

Example:
    python bible_importer.py "translations/kjv_bible.xml"

Environment Variables Required:
    - AZURE_STORAGE_ACCOUNT_NAME: Azure storage account name
    - AZURE_STORAGE_ACCOUNT_KEY or AZURE_STORAGE_CONNECTION_STRING: Authentication
    - DB_SERVER: Azure SQL server name
    - DB_DATABASE: Database name
    - DB_USERNAME, DB_PASSWORD: Database credentials (if not using Azure AD)

Optional Environment Variables:
    - AZURE_BLOB_CONTAINER_NAME: Container name (default: bible-translations)
    - DB_BATCH_SIZE: Batch size for inserts (default: 2000)
    - IMPORTER_DRY_RUN: Set to 'true' for dry run mode
    - IMPORTER_LOG_LEVEL: Logging level (default: INFO)
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Optional, Callable

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "tools"))

from tools.config import Config
from tools.blob_service import BlobStorageService
from tools.database_service import DatabaseService, VerseData
from tools.xml_parser import BibleXMLParser, XMLParsingError


class ProgressTracker:
    """Simple progress tracking and display."""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
        self.last_update = 0
    
    def update(self, current: int, total: Optional[int] = None) -> None:
        """Update progress."""
        self.current = current
        if total is not None:
            self.total = total
        
        # Update every 1% or at least every 5 seconds
        now = time.time()
        if (self.current - self.last_update >= self.total * 0.01) or (now - self.last_update >= 5):
            self._display_progress()
            self.last_update = self.current
    
    def _display_progress(self) -> None:
        """Display current progress."""
        if self.total > 0:
            percentage = (self.current / self.total) * 100
            elapsed = time.time() - self.start_time
            
            if self.current > 0:
                eta = (elapsed / self.current) * (self.total - self.current)
                print(f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%) "
                      f"- ETA: {eta:.0f}s", end='\r')
            else:
                print(f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%)", end='\r')
    
    def finish(self) -> None:
        """Mark progress as complete."""
        elapsed = time.time() - self.start_time
        print(f"\n{self.description} completed in {elapsed:.2f}s")


class BibleImporter:
    """Main Bible importer class."""
    
    def __init__(self, config: Config):
        """
        Initialize the Bible importer.
        
        Args:
            config: Configuration settings
        """
        self.config = config
        self.blob_service = BlobStorageService(config.azure)
        self.db_service = DatabaseService(config.database)
        self.xml_parser = BibleXMLParser(config.importer)
        self.logger = logging.getLogger(__name__)
    
    def import_bible_xml(self, xml_filename: str) -> bool:
        """
        Import a Bible XML file from Azure Blob Storage to Azure SQL Database.
        
        Args:
            xml_filename: Name of the XML file in blob storage
            
        Returns:
            True if import was successful, False otherwise
        """
        start_time = time.time()
        translation_id = None
        
        try:
            self.logger.info(f"Starting import of '{xml_filename}'")
            
            # Step 1: Validate file exists
            if not self.blob_service.blob_exists(xml_filename):
                self.logger.error(f"File '{xml_filename}' not found in blob storage")
                return False
            
            # Step 2: Get file metadata
            metadata = self.blob_service.get_blob_metadata(xml_filename)
            file_size_mb = metadata['size'] / (1024 * 1024)
            self.logger.info(f"File size: {file_size_mb:.2f} MB")
            
            # Step 3: Download file with progress tracking
            progress_tracker = ProgressTracker(int(metadata['size']), "Downloading")
            
            if self.config.importer.show_progress:
                xml_stream = self.blob_service.download_blob_with_progress(
                    xml_filename, 
                    lambda current, total: progress_tracker.update(current, total)
                )
                progress_tracker.finish()
            else:
                xml_stream = self.blob_service.download_blob_to_stream(xml_filename)
            
            # Step 4: Parse XML
            self.logger.info("Parsing XML file")
            parsed_data = self.xml_parser.parse_bible_xml(xml_stream, file_size_mb)
            
            self.logger.info(f"Parsed {parsed_data.statistics['total_verses']} verses "
                           f"from {parsed_data.statistics['total_books']} books")
            
            if self.config.importer.dry_run:
                self.logger.info("DRY RUN MODE - No database changes will be made")
                self._print_import_summary(parsed_data, 0, 0, 0)
                return True
            
            # Step 5: Database operations
            self.logger.info("Starting database import")
            
            # Create or get translation
            translation_id = self.db_service.get_or_create_translation(parsed_data.translation)
            
            # Create or get books
            book_code_to_id = self.db_service.get_or_create_books(parsed_data.books)
            
            # Update verse data with actual IDs
            verses_with_ids = []
            for verse in parsed_data.verses:
                # Use the book_code from the verse data if available
                book_id = None
                if hasattr(verse, 'book_code') and verse.book_code and verse.book_code in book_code_to_id:
                    book_id = book_code_to_id[verse.book_code]
                else:
                    # Fallback: use the first available book (this shouldn't happen with proper parsing)
                    for book in parsed_data.books:
                        if book.code in book_code_to_id:
                            book_id = book_code_to_id[book.code]
                            break
                
                if book_id:
                    verses_with_ids.append(VerseData(
                        translation_id=translation_id,
                        book_id=book_id,
                        chapter_number=verse.chapter_number,
                        verse_number=verse.verse_number,
                        text=verse.text
                    ))
            
            # Step 6: Insert verses with progress tracking
            verse_progress = ProgressTracker(len(verses_with_ids), "Inserting verses")
            
            progress_callback = None
            if self.config.importer.show_progress:
                progress_callback = lambda current, total: verse_progress.update(current, total)
            
            inserted_count, skipped_count = self.db_service.insert_verses_batch(
                verses_with_ids, 
                progress_callback
            )
            
            if self.config.importer.show_progress:
                verse_progress.finish()
            
            # Step 7: Get final statistics
            stats = self.db_service.get_translation_statistics(translation_id)
            
            # Success summary
            elapsed_time = time.time() - start_time
            self.logger.info(f"Import completed successfully in {elapsed_time:.2f} seconds")
            self._print_import_summary(parsed_data, inserted_count, skipped_count, elapsed_time, stats)
            
            return True
            
        except XMLParsingError as e:
            self.logger.error(f"XML parsing error: {e}")
            self._cleanup_on_error(translation_id)
            return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error during import: {e}")
            if not self.config.importer.continue_on_error:
                self._cleanup_on_error(translation_id)
            return False
    
    def _cleanup_on_error(self, translation_id: Optional[int]) -> None:
        """Clean up database records on error."""
        if translation_id and not self.config.importer.dry_run:
            try:
                self.logger.info(f"Cleaning up incomplete translation {translation_id}")
                self.db_service.cleanup_incomplete_translation(translation_id)
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")
    
    def _print_import_summary(self, parsed_data, inserted_count: int, skipped_count: int, 
                            elapsed_time: float, db_stats: Optional[dict] = None) -> None:
        """Print a summary of the import operation."""
        print("\n" + "="*60)
        print("IMPORT SUMMARY")
        print("="*60)
        print(f"Translation: {parsed_data.translation.name}")
        print(f"Language: {parsed_data.translation.language_code}")
        print(f"Identifier: {parsed_data.translation.identifier}")
        
        if parsed_data.translation.license:
            print(f"License: {parsed_data.translation.license}")
        
        print(f"\nParsed Data:")
        print(f"  Books: {parsed_data.statistics['total_books']}")
        print(f"  Verses: {parsed_data.statistics['total_verses']}")
        print(f"  Parsing method: {parsed_data.statistics['parsing_method']}")
        
        if not self.config.importer.dry_run:
            print(f"\nDatabase Operations:")
            print(f"  Verses inserted: {inserted_count}")
            print(f"  Verses skipped: {skipped_count}")
            
            if db_stats:
                print(f"  Total verses in translation: {db_stats['verse_count']}")
                print(f"  Total books in translation: {db_stats['book_count']}")
                print(f"  Total chapters in translation: {db_stats['chapter_count']}")
        
        if elapsed_time > 0:
            print(f"\nPerformance:")
            print(f"  Total time: {elapsed_time:.2f} seconds")
            if not self.config.importer.dry_run and inserted_count > 0:
                print(f"  Verses per second: {inserted_count / elapsed_time:.1f}")
        
        print("="*60)
    
    def test_connections(self) -> bool:
        """Test all connections."""
        self.logger.info("Testing connections...")
        
        # Test blob storage
        try:
            blobs = self.blob_service.list_blobs()
            self.logger.info(f"Blob storage connection OK ({len(blobs)} files found)")
        except Exception as e:
            self.logger.error(f"Blob storage connection failed: {e}")
            return False
        
        # Test database
        if not self.db_service.test_connection():
            self.logger.error("Database connection failed")
            return False
        
        self.logger.info("All connections successful")
        return True


def setup_logging(config: Config) -> None:
    """Set up logging configuration."""
    log_level = getattr(logging, config.importer.log_level, logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Add file handler if specified
    if config.importer.log_file:
        file_handler = logging.FileHandler(config.importer.log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logging.getLogger().addHandler(file_handler)
    
    # Suppress Azure SDK noise
    logging.getLogger('azure').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Import Bible XML from Azure Blob Storage to Azure SQL Database",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "xml_filename",
        help="Name of the XML file in Azure Blob Storage"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate without making database changes"
    )
    
    parser.add_argument(
        "--test-connections",
        action="store_true",
        help="Test connections and exit"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override logging level"
    )
    
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress tracking"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = Config()
        
        # Override config with command line arguments
        if args.dry_run:
            config.importer.dry_run = True
        
        if args.log_level:
            config.importer.log_level = args.log_level
        
        if args.no_progress:
            config.importer.show_progress = False
        
        # Validate configuration
        config.validate()
        
        # Set up logging
        setup_logging(config)
        
        # Create importer
        importer = BibleImporter(config)
        
        # Test connections if requested
        if args.test_connections:
            if importer.test_connections():
                print("All connections successful!")
                return 0
            else:
                print("Connection test failed!")
                return 1
        
        # Perform import
        success = importer.import_bible_xml(args.xml_filename)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nImport cancelled by user")
        return 1
        
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.exception("Fatal error occurred")
        return 1


if __name__ == "__main__":
    sys.exit(main())