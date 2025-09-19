"""
Enhanced logging and error handling utilities for Bible XML importer.

This module provides comprehensive logging, error tracking, and monitoring
capabilities for the Bible import process.
"""

import logging
import sys
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, TextIO
import json


@dataclass
class ErrorInfo:
    """Information about an error that occurred during import."""
    timestamp: datetime
    error_type: str
    error_message: str
    traceback_info: str
    context: Dict[str, Any] = field(default_factory=dict)
    severity: str = "ERROR"


@dataclass
class ImportMetrics:
    """Metrics and statistics for an import operation."""
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # File metrics
    file_name: str = ""
    file_size_bytes: int = 0
    download_time_seconds: float = 0.0
    
    # Parsing metrics
    parsing_time_seconds: float = 0.0
    parsing_method: str = ""
    total_verses_parsed: int = 0
    total_books_parsed: int = 0
    
    # Database metrics
    database_time_seconds: float = 0.0
    verses_inserted: int = 0
    verses_skipped: int = 0
    books_created: int = 0
    translation_id: Optional[int] = None
    
    # Error tracking
    errors: List[ErrorInfo] = field(default_factory=list)
    warnings_count: int = 0
    
    @property
    def total_time_seconds(self) -> float:
        """Get total elapsed time."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def verses_per_second(self) -> float:
        """Get verses processed per second."""
        if self.total_time_seconds > 0 and self.verses_inserted > 0:
            return self.verses_inserted / self.total_time_seconds
        return 0.0
    
    def add_error(self, error: ErrorInfo) -> None:
        """Add an error to the metrics."""
        self.errors.append(error)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_time_seconds": self.total_time_seconds,
            "file_name": self.file_name,
            "file_size_bytes": self.file_size_bytes,
            "file_size_mb": self.file_size_bytes / (1024 * 1024),
            "download_time_seconds": self.download_time_seconds,
            "parsing_time_seconds": self.parsing_time_seconds,
            "parsing_method": self.parsing_method,
            "total_verses_parsed": self.total_verses_parsed,
            "total_books_parsed": self.total_books_parsed,
            "database_time_seconds": self.database_time_seconds,
            "verses_inserted": self.verses_inserted,
            "verses_skipped": self.verses_skipped,
            "verses_per_second": self.verses_per_second,
            "books_created": self.books_created,
            "translation_id": self.translation_id,
            "errors_count": len(self.errors),
            "warnings_count": self.warnings_count,
            "errors": [
                {
                    "timestamp": error.timestamp.isoformat(),
                    "type": error.error_type,
                    "message": error.error_message,
                    "severity": error.severity,
                    "context": error.context
                }
                for error in self.errors
            ]
        }


class MetricsCollector:
    """Collects and tracks metrics during import operations."""
    
    def __init__(self):
        self.current_metrics: Optional[ImportMetrics] = None
        self.logger = logging.getLogger(__name__)
    
    def start_import(self, file_name: str) -> ImportMetrics:
        """Start tracking metrics for a new import."""
        self.current_metrics = ImportMetrics(
            start_time=datetime.now(),
            file_name=file_name
        )
        self.logger.info(f"Started metrics collection for {file_name}")
        return self.current_metrics
    
    def finish_import(self) -> Optional[ImportMetrics]:
        """Finish tracking metrics."""
        if self.current_metrics:
            self.current_metrics.end_time = datetime.now()
            self.logger.info(f"Finished metrics collection - total time: {self.current_metrics.total_time_seconds:.2f}s")
        return self.current_metrics
    
    def record_error(self, error: Exception, context: Dict[str, Any] = None, 
                    severity: str = "ERROR") -> None:
        """Record an error in the metrics."""
        if self.current_metrics:
            error_info = ErrorInfo(
                timestamp=datetime.now(),
                error_type=type(error).__name__,
                error_message=str(error),
                traceback_info=traceback.format_exc(),
                context=context or {},
                severity=severity
            )
            self.current_metrics.add_error(error_info)
            
            if severity == "WARNING":
                self.current_metrics.warnings_count += 1
    
    @contextmanager
    def time_operation(self, operation_name: str):
        """Context manager to time an operation."""
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            self.logger.debug(f"{operation_name} took {elapsed:.3f} seconds")
            
            if self.current_metrics:
                if operation_name == "download":
                    self.current_metrics.download_time_seconds = elapsed
                elif operation_name == "parsing":
                    self.current_metrics.parsing_time_seconds = elapsed
                elif operation_name == "database":
                    self.current_metrics.database_time_seconds = elapsed


class StructuredLogger:
    """Enhanced logger with structured logging capabilities."""
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.metrics_collector = MetricsCollector()
        self._setup_structured_logging(log_file)
    
    def _setup_structured_logging(self, log_file: Optional[str]) -> None:
        """Set up structured logging with JSON format option."""
        # Create custom formatter for structured logs
        class StructuredFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                # Add extra fields if present
                if hasattr(record, 'extra_fields'):
                    log_entry.update(record.extra_fields)
                
                return json.dumps(log_entry)
        
        # Set up file handler with structured format if log file specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(file_handler)
    
    def log_with_context(self, level: int, message: str, **context) -> None:
        """Log with additional context fields."""
        extra = {"extra_fields": context}
        self.logger.log(level, message, extra=extra)
    
    def info_with_context(self, message: str, **context) -> None:
        """Log info message with context."""
        self.log_with_context(logging.INFO, message, **context)
    
    def error_with_context(self, message: str, **context) -> None:
        """Log error message with context."""
        self.log_with_context(logging.ERROR, message, **context)
    
    def warning_with_context(self, message: str, **context) -> None:
        """Log warning message with context."""
        self.log_with_context(logging.WARNING, message, **context)


class ErrorRecovery:
    """Handles error recovery and retry logic."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def retry_on_failure(self, operation_name: str, 
                        retryable_exceptions: tuple = (Exception,)):
        """Retry an operation on failure with exponential backoff."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"Attempting {operation_name} (attempt {attempt + 1}/{self.max_retries + 1})")
                yield attempt
                return  # Success, exit retry loop
                
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    self.logger.error(f"{operation_name} failed after {self.max_retries + 1} attempts")
                    raise
                
                delay = self.base_delay * (2 ** attempt)  # Exponential backoff
                self.logger.warning(f"{operation_name} failed (attempt {attempt + 1}): {e}")
                self.logger.info(f"Retrying in {delay:.1f} seconds...")
                time.sleep(delay)


class HealthChecker:
    """Performs health checks on system components."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_memory_usage(self, threshold_mb: int = 500) -> bool:
        """Check if memory usage is within acceptable limits."""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            
            if memory_mb > threshold_mb:
                self.logger.warning(f"High memory usage: {memory_mb:.1f} MB (threshold: {threshold_mb} MB)")
                return False
            
            self.logger.debug(f"Memory usage OK: {memory_mb:.1f} MB")
            return True
            
        except ImportError:
            self.logger.warning("psutil not available for memory monitoring")
            return True
        except Exception as e:
            self.logger.error(f"Error checking memory usage: {e}")
            return True
    
    def check_disk_space(self, path: str = ".", min_free_gb: float = 1.0) -> bool:
        """Check if sufficient disk space is available."""
        try:
            import shutil
            total, used, free = shutil.disk_usage(path)
            free_gb = free / (1024 ** 3)
            
            if free_gb < min_free_gb:
                self.logger.warning(f"Low disk space: {free_gb:.2f} GB free (minimum: {min_free_gb} GB)")
                return False
            
            self.logger.debug(f"Disk space OK: {free_gb:.2f} GB free")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking disk space: {e}")
            return True


def save_metrics_report(metrics: ImportMetrics, output_file: Optional[str] = None) -> None:
    """Save metrics report to file."""
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"bible_import_metrics_{timestamp}.json"
    
    try:
        with open(output_file, 'w') as f:
            json.dump(metrics.to_dict(), f, indent=2)
        
        logging.getLogger(__name__).info(f"Metrics report saved to {output_file}")
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save metrics report: {e}")


def print_metrics_summary(metrics: ImportMetrics) -> None:
    """Print a formatted summary of import metrics."""
    print("\n" + "="*80)
    print("IMPORT METRICS SUMMARY")
    print("="*80)
    
    print(f"File: {metrics.file_name}")
    print(f"File Size: {metrics.file_size_bytes / (1024*1024):.2f} MB")
    print(f"Total Time: {metrics.total_time_seconds:.2f} seconds")
    
    print(f"\nTiming Breakdown:")
    print(f"  Download: {metrics.download_time_seconds:.2f}s")
    print(f"  Parsing: {metrics.parsing_time_seconds:.2f}s")
    print(f"  Database: {metrics.database_time_seconds:.2f}s")
    
    print(f"\nData Processing:")
    print(f"  Books Parsed: {metrics.total_books_parsed}")
    print(f"  Verses Parsed: {metrics.total_verses_parsed}")
    print(f"  Verses Inserted: {metrics.verses_inserted}")
    print(f"  Verses Skipped: {metrics.verses_skipped}")
    
    if metrics.verses_per_second > 0:
        print(f"  Processing Rate: {metrics.verses_per_second:.1f} verses/second")
    
    print(f"\nError Summary:")
    print(f"  Errors: {len(metrics.errors)}")
    print(f"  Warnings: {metrics.warnings_count}")
    
    if metrics.errors:
        print(f"\nError Details:")
        for i, error in enumerate(metrics.errors[:5], 1):  # Show first 5 errors
            print(f"  {i}. {error.error_type}: {error.error_message}")
        
        if len(metrics.errors) > 5:
            print(f"  ... and {len(metrics.errors) - 5} more errors")
    
    print("="*80)