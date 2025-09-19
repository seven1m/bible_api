# Bible XML Importer Documentation

A production-ready Python script for importing Bible XML files from Azure Blob Storage into Azure SQL Database with comprehensive error handling, progress tracking, and performance optimization.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [XML Format Support](#xml-format-support)
- [Performance Tuning](#performance-tuning)
- [Monitoring and Logging](#monitoring-and-logging)
- [Error Handling](#error-handling)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

## Features

### Core Functionality
- ✅ **Azure Integration**: Native support for Azure Blob Storage and Azure SQL Database
- ✅ **Multiple Authentication**: Managed Identity, connection strings, and storage keys
- ✅ **XML Format Support**: OSIS, generic Bible XML, and auto-detection
- ✅ **Streaming Parser**: Handles large XML files efficiently with streaming/in-memory parsing
- ✅ **Batch Processing**: Optimized batch inserts with configurable batch sizes
- ✅ **Progress Tracking**: Real-time progress indicators and ETA calculations
- ✅ **Duplicate Handling**: Smart duplicate detection and skipping
- ✅ **Transaction Safety**: Full rollback on errors with cleanup mechanisms

### Performance & Reliability
- ✅ **Connection Pooling**: Efficient database connection management
- ✅ **Retry Logic**: Exponential backoff for transient failures
- ✅ **Memory Management**: Configurable memory limits and monitoring
- ✅ **Health Checks**: System resource monitoring and validation
- ✅ **Comprehensive Logging**: Structured logging with metrics collection
- ✅ **Dry Run Mode**: Safe testing without database modifications

## Prerequisites

### System Requirements
- Python 3.8 or higher
- Windows, Linux, or macOS
- Minimum 2GB RAM (4GB+ recommended for large files)
- Azure SQL Database with appropriate schema
- Azure Blob Storage account

### Azure Resources
1. **Azure SQL Database** with the Bible schema (see [sql/db_creation_script.sql](sql/db_creation_script.sql))
2. **Azure Blob Storage** account with container for XML files
3. **Appropriate permissions** for database and storage access

## Installation

### 1. Clone and Install Dependencies

```bash
# Navigate to the project directory
cd bible_api

# Install Python dependencies
pip install -r requirements.txt

# For development/testing, also install dev dependencies
pip install -r requirements-dev.txt
```

### 2. Database Setup

Run the database creation script to set up the required schema:

```sql
-- Execute the contents of sql/db_creation_script.sql
-- This creates Translation, Book, and Verse tables with indexes
```

### 3. Verify Installation

```bash
# Test the installation
python bible_importer.py --test-connections
```

## Configuration

The importer uses environment variables for configuration. Create a `.env` file or set these in your environment:

### Required Variables

```bash
# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account
AZURE_STORAGE_ACCOUNT_KEY=your_storage_key
# OR
AZURE_STORAGE_CONNECTION_STRING=your_connection_string

# Azure SQL Database
DB_SERVER=your_server.database.windows.net
DB_DATABASE=your_database_name
DB_USERNAME=your_username
DB_PASSWORD=your_password
```

### Optional Variables

```bash
# Azure Configuration
AZURE_BLOB_CONTAINER_NAME=bible-translations  # default
AZURE_USE_MANAGED_IDENTITY=true               # default

# Database Configuration
DB_DRIVER="ODBC Driver 18 for SQL Server"     # default
DB_CONNECTION_TIMEOUT=30                       # seconds
DB_COMMAND_TIMEOUT=300                         # seconds
DB_BATCH_SIZE=2000                            # records per batch
DB_MAX_RETRIES=3                              # retry attempts
DB_USE_AZURE_AD=true                          # use Azure AD auth

# Importer Settings
IMPORTER_DRY_RUN=false                        # default
IMPORTER_SKIP_EXISTING=true                   # default
IMPORTER_SHOW_PROGRESS=true                   # default
IMPORTER_LOG_LEVEL=INFO                       # DEBUG,INFO,WARNING,ERROR
IMPORTER_LOG_FILE=bible_import.log            # optional
IMPORTER_STREAMING_THRESHOLD_MB=100           # use streaming for larger files
IMPORTER_MEMORY_LIMIT_MB=500                  # memory usage limit
IMPORTER_CONTINUE_ON_ERROR=false              # stop on errors
IMPORTER_MAX_ERRORS=100                       # maximum error count
```

### Configuration File Example

```bash
# .env file example
AZURE_STORAGE_ACCOUNT_NAME=mybiblestore
AZURE_STORAGE_ACCOUNT_KEY=abcd1234...
AZURE_BLOB_CONTAINER_NAME=bible-translations

DB_SERVER=mybibledb.database.windows.net
DB_DATABASE=BibleAPI
DB_USERNAME=bibleuser
DB_PASSWORD=SecurePassword123!

IMPORTER_LOG_LEVEL=INFO
IMPORTER_BATCH_SIZE=3000
```

## Usage

### Basic Usage

```bash
# Import a Bible XML file
python bible_importer.py "translations/kjv_bible.xml"

# Dry run (parse and validate without database changes)
python bible_importer.py --dry-run "translations/kjv_bible.xml"

# Test all connections
python bible_importer.py --test-connections
```

### Advanced Usage

```bash
# Import with custom settings
python bible_importer.py \
    --log-level DEBUG \
    --no-progress \
    "translations/esv_bible.xml"

# Dry run with detailed logging
python bible_importer.py \
    --dry-run \
    --log-level DEBUG \
    "translations/new_translation.xml"
```

### Command Line Options

```
positional arguments:
  xml_filename          Name of the XML file in Azure Blob Storage

optional arguments:
  -h, --help           Show help message and exit
  --dry-run            Parse and validate without making database changes
  --test-connections   Test connections and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                       Override logging level
  --no-progress        Disable progress tracking
```

## XML Format Support

The importer supports multiple XML formats with automatic detection:

### OSIS Format
```xml
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
  <osisText>
    <header>
      <work osisWork="KJV">
        <title>King James Version</title>
        <language ident="en"/>
      </work>
    </header>
    <div type="book" osisID="Gen">
      <div type="chapter" osisID="Gen.1">
        <verse osisID="Gen.1.1">In the beginning God created...</verse>
      </div>
    </div>
  </osisText>
</osis>
```

### Generic Bible Format
```xml
<bible version="ESV" language="en">
  <book code="GEN" name="Genesis">
    <chapter number="1">
      <verse number="1">In the beginning, God created...</verse>
    </chapter>
  </book>
</bible>
```

### Auto-Detection
The parser automatically detects the XML format and applies appropriate parsing strategies.

## Performance Tuning

### Batch Size Optimization

```bash
# For small files (< 50MB)
DB_BATCH_SIZE=1000

# For medium files (50-200MB)
DB_BATCH_SIZE=2000

# For large files (> 200MB)
DB_BATCH_SIZE=5000
```

### Memory Management

```bash
# For systems with limited RAM (< 4GB)
IMPORTER_STREAMING_THRESHOLD_MB=50
IMPORTER_MEMORY_LIMIT_MB=200

# For high-memory systems (8GB+)
IMPORTER_STREAMING_THRESHOLD_MB=200
IMPORTER_MEMORY_LIMIT_MB=1000
```

### Connection Tuning

```bash
# For high-latency connections
DB_CONNECTION_TIMEOUT=60
DB_COMMAND_TIMEOUT=600

# For fast, local connections
DB_CONNECTION_TIMEOUT=15
DB_COMMAND_TIMEOUT=120
```

## Monitoring and Logging

### Log Levels
- **DEBUG**: Detailed execution information, performance metrics
- **INFO**: General progress, major operations (default)
- **WARNING**: Non-critical issues, fallback operations
- **ERROR**: Critical errors, operation failures

### Metrics Collection

The importer automatically collects comprehensive metrics:

```json
{
  "start_time": "2024-01-15T10:30:00",
  "total_time_seconds": 45.67,
  "file_size_mb": 125.4,
  "verses_inserted": 31102,
  "verses_per_second": 681.2,
  "parsing_method": "streaming",
  "errors_count": 0
}
```

### Log File Format

```
2024-01-15 10:30:00,123 - bible_importer - INFO - Starting import of 'kjv_bible.xml'
2024-01-15 10:30:05,456 - blob_service - INFO - Downloaded blob (125.4 MB)
2024-01-15 10:30:15,789 - xml_parser - INFO - Parsed 31102 verses from 66 books
2024-01-15 10:30:45,012 - database_service - INFO - Import completed: 31102 inserted
```

## Error Handling

### Automatic Recovery
- **Connection failures**: Exponential backoff retry
- **Transient database errors**: Automatic retry with rollback
- **Memory issues**: Automatic fallback to streaming mode
- **Malformed XML**: Graceful error reporting with context

### Error Types and Solutions

| Error Type | Cause | Solution |
|------------|-------|----------|
| `ConnectionError` | Network/Azure connectivity | Check network, credentials |
| `XMLParsingError` | Invalid XML format | Verify file format, check encoding |
| `DatabaseError` | SQL server issues | Check permissions, connection string |
| `MemoryError` | Large file processing | Reduce batch size, enable streaming |
| `AuthenticationError` | Invalid credentials | Verify Azure credentials |

### Error Recovery Example

```python
# The importer automatically handles errors like this:
try:
    # Attempt database operation
    result = db_service.insert_verses_batch(verses)
except pyodbc.Error as e:
    # Automatic retry with exponential backoff
    logger.warning(f"Database error, retrying: {e}")
    time.sleep(retry_delay)
    # Retry operation...
```

## Troubleshooting

### Common Issues

#### 1. Connection Timeout Errors
```bash
# Symptoms: Timeout during connection
# Solution: Increase timeout values
DB_CONNECTION_TIMEOUT=60
DB_COMMAND_TIMEOUT=300
```

#### 2. Memory Errors with Large Files
```bash
# Symptoms: OutOfMemoryError or slow performance
# Solution: Enable streaming mode
IMPORTER_STREAMING_THRESHOLD_MB=50
IMPORTER_MEMORY_LIMIT_MB=200
```

#### 3. Azure Authentication Failures
```bash
# Symptoms: Authentication errors
# Solution: Verify credentials and permissions
az login  # For Azure CLI authentication
# Or provide explicit credentials
AZURE_STORAGE_ACCOUNT_KEY=your_key
```

#### 4. Slow Import Performance
```bash
# Solutions:
# 1. Increase batch size
DB_BATCH_SIZE=5000

# 2. Disable progress tracking
IMPORTER_SHOW_PROGRESS=false

# 3. Use connection pooling
DB_POOL_SIZE=10
```

#### 5. XML Parsing Failures
```
# Symptoms: XMLParsingError
# Solutions:
# 1. Check file encoding (should be UTF-8)
# 2. Validate XML structure
# 3. Enable debug logging for details
IMPORTER_LOG_LEVEL=DEBUG
```

### Debug Mode

Enable comprehensive debugging:

```bash
python bible_importer.py \
    --log-level DEBUG \
    --dry-run \
    "problematic_file.xml" > debug.log 2>&1
```

### Performance Analysis

```bash
# Enable metrics collection
python -c "
import time
from tools.logging_utils import MetricsCollector
collector = MetricsCollector()
# ... run import ...
print(collector.current_metrics.to_dict())
"
```

## API Reference

### Core Classes

#### `BibleImporter`
Main importer class orchestrating the entire process.

```python
from bible_importer import BibleImporter
from tools.config import Config

config = Config()
importer = BibleImporter(config)
success = importer.import_bible_xml("bible.xml")
```

#### `BlobStorageService`
Handles Azure Blob Storage operations.

```python
from tools.blob_service import BlobStorageService
from tools.config import AzureConfig

service = BlobStorageService(config.azure)
xml_stream = service.download_blob_to_stream("bible.xml")
```

#### `DatabaseService`
Manages database operations and batch processing.

```python
from tools.database_service import DatabaseService

db_service = DatabaseService(config.database)
translation_id = db_service.get_or_create_translation(translation_data)
```

#### `BibleXMLParser`
Parses XML files with format auto-detection.

```python
from tools.xml_parser import BibleXMLParser

parser = BibleXMLParser(config.importer)
parsed_data = parser.parse_bible_xml(xml_stream)
```

### Configuration Classes

#### `Config`
Main configuration class combining all settings.

```python
from tools.config import Config

config = Config()
config.validate()  # Validate all settings
```

#### `AzureConfig`
Azure-specific configuration.

#### `DatabaseConfig`
Database connection and operation settings.

#### `ImporterConfig`
Import process configuration.

### Utility Classes

#### `MetricsCollector`
Collects performance and operation metrics.

#### `ErrorRecovery`
Handles retry logic and error recovery.

#### `HealthChecker`
Monitors system health and resources.

---

## Support and Contributing

For issues, feature requests, or contributions, please refer to the project repository.

### Version History
- **v1.0.0**: Initial release with comprehensive import functionality
- **v1.1.0**: Added streaming support for large files
- **v1.2.0**: Enhanced error handling and metrics collection

### License
See LICENSE file for licensing information.