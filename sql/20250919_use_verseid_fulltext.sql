/* Migration: Switch full-text key from FTKey to VerseId
   Date: 2025-09-19 (Revised to avoid wrapping full-text operations in user transaction)
   Adds automatic creation of BibleCatalog full-text catalog if missing.
   Safe to rerun (guards included). Adjust LANGUAGE code (1033) if needed.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

PRINT 'Step 0: Ensure full-text feature & catalog exist...';
IF NOT EXISTS (SELECT * FROM sys.fulltext_catalogs WHERE name = 'BibleCatalog')
BEGIN
    PRINT 'Creating full-text catalog BibleCatalog...';
    CREATE FULLTEXT CATALOG BibleCatalog WITH ACCENT_SENSITIVITY = OFF;
END
ELSE
BEGIN
    PRINT 'Full-text catalog BibleCatalog already exists.';
END
GO

PRINT 'Step 1: Drop full-text index if it exists (no user transaction)...';
IF EXISTS (
    SELECT 1 FROM sys.fulltext_indexes fi
    JOIN sys.objects o ON fi.object_id = o.object_id
    WHERE o.name = 'Verse'
)
BEGIN
    DROP FULLTEXT INDEX ON dbo.Verse;
END
GO

PRINT 'Step 2: Begin transactional structural changes (indexes/column)...';
BEGIN TRANSACTION;

PRINT 'Dropping unique index on FTKey if it exists...';
IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_Verse_FTKey' AND object_id = OBJECT_ID('dbo.Verse'))
BEGIN
    DROP INDEX UX_Verse_FTKey ON dbo.Verse;
END

PRINT 'Dropping FTKey column if it exists...';
IF COL_LENGTH('dbo.Verse','FTKey') IS NOT NULL
BEGIN
    ALTER TABLE dbo.Verse DROP COLUMN FTKey;
END

PRINT 'Creating unique nonclustered index on VerseId for full-text key (if missing)...';
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_Verse_FT' AND object_id = OBJECT_ID('dbo.Verse'))
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_Verse_FT ON dbo.Verse(VerseId);
END

COMMIT TRANSACTION;
GO

PRINT 'Step 3: Create full-text index on VerseId key (no user transaction)...';
IF NOT EXISTS (
    SELECT 1 FROM sys.fulltext_indexes fi
    JOIN sys.objects o ON fi.object_id = o.object_id
    WHERE o.name = 'Verse'
)
BEGIN
    CREATE FULLTEXT INDEX ON dbo.Verse (Text LANGUAGE 1033)
        KEY INDEX UX_Verse_FT
        ON BibleCatalog
        WITH CHANGE_TRACKING MANUAL; -- Switch to AUTO later if desired
END
ELSE
BEGIN
    PRINT 'Full-text index already exists; skipping creation.';
END
GO

PRINT 'Full-text index switched to VerseId successfully.';

/* After bulk load, run (separately):
   ALTER FULLTEXT INDEX ON dbo.Verse START FULL POPULATION;
   -- Optional (after population complete):
   ALTER FULLTEXT INDEX ON dbo.Verse SET CHANGE_TRACKING AUTO;

   To verify population status:
   SELECT fulltext_catalog_id, name, is_default, populate_status, item_count
   FROM sys.fulltext_catalogs WHERE name = 'BibleCatalog';
*/

/* Permission notes:
   - Requires CREATE FULLTEXT CATALOG / INDEX rights (db_owner typically sufficient).
   - If you still receive catalog/permission errors, confirm Full-Text Search feature is installed on the SQL Server instance.
*/
