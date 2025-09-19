# Bible Importer Console Application

A standalone console application that retrieves XML files from Azure Blob Storage, parses their contents, and imports the data into Azure SQL tables.

## Features

- **Console Interface**: Interactive XML filename input
- **Azure Blob Storage Integration**: Retrieves XML files by exact filename
- **USFX XML Parsing**: Parses entire Bible translations with complete verse structure
- **Azure SQL Database Import**: Imports complete translations using the precise schema provided
- **Error Handling**: JSON formatted error and success responses
- **Configuration Support**: JSON and INI configuration file support

## Configuration

Create a configuration file in the root directory (same directory as the executable) with one of these formats:

### JSON Format (`config.json`)

```json
{
  "AzureBlobConnectionString": "DefaultEndpointsProtocol=https;AccountName=your_account;AccountKey=your_key;EndpointSuffix=core.windows.net",
  "BlobContainerName": "bible-translations",
  "SqlConnectionString": "Server=your_server;Database=your_database;Trusted_Connection=true;TrustServerCertificate=true;"
}
```

### INI Format (`config.ini`)

```ini
[BibleImporter]
AzureBlobConnectionString=DefaultEndpointsProtocol=https;AccountName=your_account;AccountKey=your_key;EndpointSuffix=core.windows.net
BlobContainerName=bible-translations
SqlConnectionString=Server=your_server;Database=your_database;Trusted_Connection=true;TrustServerCertificate=true;
```

## Configuration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `AzureBlobConnectionString` | Yes | Azure Storage connection string for Bible XML files |
| `BlobContainerName` | Yes | Container name containing Bible translations |
| `SqlConnectionString` | Yes | Azure SQL database connection string |

## Database Schema

The application expects the following SQL Server tables to exist:

```sql
CREATE TABLE dbo.Translation (
    TranslationId INT IDENTITY(1,1) PRIMARY KEY,
    Identifier NVARCHAR(32) NOT NULL UNIQUE,
    Name NVARCHAR(128) NOT NULL,
    LanguageCode NVARCHAR(8) NOT NULL,
    License NVARCHAR(256) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE dbo.Book (
    BookId INT IDENTITY(1,1) PRIMARY KEY,
    Code CHAR(3) NOT NULL UNIQUE,
    Name NVARCHAR(64) NOT NULL,
    Testament CHAR(2) NULL
);

CREATE TABLE dbo.Verse (
    VerseId INT IDENTITY(1,1) PRIMARY KEY,
    TranslationId INT NOT NULL,
    BookId INT NOT NULL,
    ChapterNumber SMALLINT NOT NULL,
    VerseNumber SMALLINT NOT NULL,
    Text NVARCHAR(MAX) NOT NULL,
    CONSTRAINT UQ_Verse UNIQUE (TranslationId, BookId, ChapterNumber, VerseNumber),
    CONSTRAINT FK_Verse_Translation FOREIGN KEY (TranslationId) REFERENCES dbo.Translation(TranslationId) ON DELETE CASCADE,
    CONSTRAINT FK_Verse_Book FOREIGN KEY (BookId) REFERENCES dbo.Book(BookId) ON DELETE CASCADE
);
```

## XML Format Support

The application parses USFX (Unified Standard Format XML) files with this structure:

```xml
<usfx xmlns:ns0="http://ebt.cx/usfx/usfx-2005-09-08.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="usfx-2005-09-08.xsd">
  <book id="GEN">
    ...
    <v id="1"/>Verse text...
    ...
  </book>
</usfx>
```

## Usage

1. **Build the application**:
   ```bash
   dotnet build
   ```

2. **Create your configuration file** (`config.json` or `config.ini`) in the output directory

3. **Run the application**:
   ```bash
   dotnet run
   ```

4. **Enter the XML filename** when prompted (e.g., "web.xml", "kjv.xml", "asv.xml")

**Note**: The application now imports entire Bible translations from XML files. Provide the exact filename (including .xml extension) of the translation file stored in your Azure Blob Storage container. This imports all books and verses from that translation into the database.

## Output Formats

### Success Response
```json
{
  "books_copied": 66,
  "verses_copied": 31102
}
```

### Error Response
```json
{
  "error": "XML file not found: invalid_filename.xml"
}
```

## Error Handling

The application handles various error scenarios:

- **Missing Configuration**: Invalid or missing configuration file
- **Connection Failures**: Azure Blob Storage or SQL Database connection issues
- **File Not Found**: XML file not found with the specified filename
- **Invalid XML**: Malformed or invalid XML content
- **Database Errors**: SQL operation failures
- **Parsing Errors**: XML parsing or data extraction issues
- **Invalid Input**: Non-XML file extensions or empty filenames

All errors are returned in JSON format with a descriptive error message and the application exits with a non-zero code.

## Development

### Building
```bash
dotnet build
```

### Running
```bash
dotnet run
```

### Dependencies
- .NET 8.0
- Azure.Storage.Blobs
- Microsoft.Data.SqlClient
- Microsoft.Extensions.Configuration
- Microsoft.Extensions.DependencyInjection
- Microsoft.Extensions.Logging

## License

This application is part of the Bible API project and follows the same licensing terms.