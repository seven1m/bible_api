# Bible XML Importer - Quick Start Guide

This guide will get you up and running with the Bible XML importer in minutes.

## 🚀 Quick Setup (5 minutes)

### 1. Prerequisites Check
- ✅ Python 3.8+ installed
- ✅ Azure SQL Database with Bible schema
- ✅ Azure Blob Storage account
- ✅ XML file uploaded to blob storage

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy the example configuration
cp bible_importer.env.example .env

# Edit .env with your actual values
# Minimum required:
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account
AZURE_STORAGE_ACCOUNT_KEY=your_key
DB_SERVER=your_server.database.windows.net
DB_DATABASE=your_database
DB_USERNAME=your_username
DB_PASSWORD=your_password
```

### 4. Test Setup
```bash
# Test all connections
python bible_importer.py --test-connections
```

### 5. Import Your First Bible
```bash
# Dry run first (safe, no database changes)
python bible_importer.py --dry-run "your_bible.xml"

# If successful, do the actual import
python bible_importer.py "your_bible.xml"
```

## 📋 Common Use Cases

### Development/Testing
```bash
# Safe testing without database changes
python bible_importer.py --dry-run --log-level DEBUG "test_bible.xml"
```

### Production Import
```bash
# Standard production import
python bible_importer.py "production_bible.xml"
```

### Large File Import
```bash
# For files > 100MB, automatically uses streaming
# No special configuration needed
python bible_importer.py "large_bible.xml"
```

### Troubleshooting
```bash
# Debug mode with detailed logging
python bible_importer.py --log-level DEBUG "problematic_bible.xml" 2>&1 | tee debug.log
```

## 🔧 Quick Configuration Reference

### Minimal Configuration (.env)
```bash
# Required minimum
AZURE_STORAGE_ACCOUNT_NAME=mystorageaccount
AZURE_STORAGE_ACCOUNT_KEY=abc123...
DB_SERVER=myserver.database.windows.net
DB_DATABASE=BibleAPI
DB_USERNAME=bibleuser
DB_PASSWORD=SecurePass123!
```

### Performance Optimized
```bash
# For faster imports
DB_BATCH_SIZE=5000
IMPORTER_STREAMING_THRESHOLD_MB=50
IMPORTER_SHOW_PROGRESS=true
```

### Memory Constrained
```bash
# For systems with limited RAM
DB_BATCH_SIZE=1000
IMPORTER_STREAMING_THRESHOLD_MB=25
IMPORTER_MEMORY_LIMIT_MB=200
```

## 📊 Understanding Output

### Successful Import
```
================================================================================
IMPORT SUMMARY
================================================================================
Translation: King James Version
Language: en
Identifier: KJV

Parsed Data:
  Books: 66
  Verses: 31,102
  Parsing method: streaming

Database Operations:
  Verses inserted: 31,102
  Verses skipped: 0
  Total verses in translation: 31,102
  Total books in translation: 66
  Total chapters in translation: 1,189

Performance:
  Total time: 45.67 seconds
  Verses per second: 681.2
================================================================================
```

### Progress Tracking
```
Downloading: 127MB/127MB (100.0%) - ETA: 0s
Parsing XML file
Inserting verses: 31102/31102 (100.0%)
Import completed successfully in 45.67 seconds
```

## ⚠️ Troubleshooting

### Error: "Connection failed"
1. Check your credentials in `.env`
2. Verify network connectivity
3. Test with: `python bible_importer.py --test-connections`

### Error: "File not found"
1. Verify file exists in blob storage
2. Check container name in configuration
3. Check file path/name spelling

### Error: "Memory error"
1. Reduce batch size: `DB_BATCH_SIZE=1000`
2. Enable streaming: `IMPORTER_STREAMING_THRESHOLD_MB=25`
3. Limit memory: `IMPORTER_MEMORY_LIMIT_MB=200`

### Error: "XML parsing failed"
1. Verify XML file is valid
2. Check file encoding (should be UTF-8)
3. Try with debug mode: `--log-level DEBUG`

## 🎯 Next Steps

### Production Deployment
1. Use Azure Managed Identity instead of keys
2. Set up monitoring and alerting
3. Configure automated backups
4. Set up log aggregation

### Advanced Usage
1. Read the full documentation: [docs/bible_importer.md](docs/bible_importer.md)
2. Explore configuration options
3. Set up automated imports
4. Integrate with CI/CD pipelines

### Performance Tuning
1. Benchmark with your data
2. Adjust batch sizes
3. Optimize database settings
4. Monitor resource usage

## 📞 Support

- **Documentation**: [docs/bible_importer.md](docs/bible_importer.md)
- **Example Config**: [bible_importer.env.example](bible_importer.env.example)
- **Database Schema**: [sql/db_creation_script.sql](sql/db_creation_script.sql)

---

**Happy importing! 🎉**