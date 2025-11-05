-- 1. Tables (INT VerseId)
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
    VerseId INT IDENTITY(1,1) PRIMARY KEY,          -- clustered PK
    TranslationId INT NOT NULL,
    BookId INT NOT NULL,
    ChapterNumber SMALLINT NOT NULL,
    VerseNumber SMALLINT NOT NULL,
    Text NVARCHAR(MAX) NOT NULL,
    CONSTRAINT UQ_Verse UNIQUE (TranslationId, BookId, ChapterNumber, VerseNumber),
    CONSTRAINT FK_Verse_Translation FOREIGN KEY (TranslationId) REFERENCES dbo.Translation(TranslationId) ON DELETE CASCADE,
    CONSTRAINT FK_Verse_Book FOREIGN KEY (BookId) REFERENCES dbo.Book(BookId) ON DELETE CASCADE
);

-- 2. Create a separate unique non-clustered INT column for full-text key
-- Remove IDENTITY from FTKey since VerseId is already the identity column
ALTER TABLE dbo.Verse
ADD FTKey INT NOT NULL;

-- Populate the FTKey column with VerseId values
UPDATE dbo.Verse SET FTKey = VerseId;

-- Create the unique index
CREATE UNIQUE NONCLUSTERED INDEX UX_Verse_FTKey
ON dbo.Verse(FTKey);

-- 3. Supporting indexes
CREATE NONCLUSTERED INDEX IX_Verse_ChapterLookup
ON dbo.Verse (TranslationId, BookId, ChapterNumber, VerseNumber)
INCLUDE (Text);

-- 4. Full-text catalog & index
IF NOT EXISTS (SELECT * FROM sys.fulltext_catalogs WHERE name = 'BibleCatalog')
BEGIN
    CREATE FULLTEXT CATALOG BibleCatalog WITH ACCENT_SENSITIVITY = OFF;
END;

IF NOT EXISTS (
    SELECT * 
    FROM sys.fulltext_indexes fi
    JOIN sys.objects o ON fi.object_id = o.object_id
    WHERE o.name = 'Verse'
)
BEGIN
    CREATE FULLTEXT INDEX ON dbo.Verse (Text LANGUAGE 1033)
    KEY INDEX UX_Verse_FTKey
    ON BibleCatalog
    WITH CHANGE_TRACKING AUTO;
END;