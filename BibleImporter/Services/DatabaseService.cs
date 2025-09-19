using Microsoft.Data.SqlClient;
using BibleImporter.Models;
using BibleImporter.Configuration;
using Microsoft.Extensions.Logging;
using System.Data;

namespace BibleImporter.Services
{
    /// <summary>
    /// Service for database operations related to Bible import
    /// </summary>
    public class DatabaseService
    {
        private readonly string _connectionString;
        private readonly ILogger<DatabaseService> _logger;

        public DatabaseService(ImporterConfig config, ILogger<DatabaseService> logger)
        {
            _connectionString = config.SqlConnectionString;
            _logger = logger;
        }

        /// <summary>
        /// Get or create translation in database, returns TranslationId
        /// </summary>
        public async Task<int> GetOrCreateTranslationAsync(string identifier, string name, string languageCode, string? license)
        {
            using var connection = new SqlConnection(_connectionString);
            await connection.OpenAsync();

            // Check if translation exists
            var selectSql = "SELECT TranslationId FROM dbo.Translation WHERE Identifier = @Identifier";
            using var selectCmd = new SqlCommand(selectSql, connection);
            selectCmd.Parameters.AddWithValue("@Identifier", identifier);

            var existingId = await selectCmd.ExecuteScalarAsync();
            if (existingId != null)
            {
                return (int)existingId;
            }

            // Create new translation
            var insertSql = @"
                INSERT INTO dbo.Translation (Identifier, Name, LanguageCode, License, CreatedAt) 
                VALUES (@Identifier, @Name, @LanguageCode, @License, @CreatedAt);
                SELECT SCOPE_IDENTITY();";

            using var insertCmd = new SqlCommand(insertSql, connection);
            insertCmd.Parameters.AddWithValue("@Identifier", identifier);
            insertCmd.Parameters.AddWithValue("@Name", name);
            insertCmd.Parameters.AddWithValue("@LanguageCode", languageCode);
            insertCmd.Parameters.AddWithValue("@License", license ?? (object)DBNull.Value);
            insertCmd.Parameters.AddWithValue("@CreatedAt", DateTime.UtcNow);

            var result = await insertCmd.ExecuteScalarAsync();
            return Convert.ToInt32(result);
        }

        /// <summary>
        /// Get or create book in database, returns BookId
        /// </summary>
        public async Task<int> GetOrCreateBookAsync(string code, string name, string? testament = null)
        {
            using var connection = new SqlConnection(_connectionString);
            await connection.OpenAsync();

            // Check if book exists
            var selectSql = "SELECT BookId FROM dbo.Book WHERE Code = @Code";
            using var selectCmd = new SqlCommand(selectSql, connection);
            selectCmd.Parameters.AddWithValue("@Code", code);

            var existingId = await selectCmd.ExecuteScalarAsync();
            if (existingId != null)
            {
                return (int)existingId;
            }

            // Create new book
            var insertSql = @"
                INSERT INTO dbo.Book (Code, Name, Testament) 
                VALUES (@Code, @Name, @Testament);
                SELECT SCOPE_IDENTITY();";

            using var insertCmd = new SqlCommand(insertSql, connection);
            insertCmd.Parameters.AddWithValue("@Code", code);
            insertCmd.Parameters.AddWithValue("@Name", name);
            insertCmd.Parameters.AddWithValue("@Testament", testament ?? (object)DBNull.Value);

            var result = await insertCmd.ExecuteScalarAsync();
            return Convert.ToInt32(result);
        }

        /// <summary>
        /// Insert verses in bulk for better performance
        /// </summary>
        public async Task<int> InsertVersesAsync(int translationId, int bookId, List<(short chapter, short verse, string text)> verses)
        {
            using var connection = new SqlConnection(_connectionString);
            await connection.OpenAsync();

            using var transaction = connection.BeginTransaction();
            try
            {
                int insertedCount = 0;

                foreach (var (chapter, verse, text) in verses)
                {
                    var insertSql = @"
                        INSERT INTO dbo.Verse (TranslationId, BookId, ChapterNumber, VerseNumber, Text) 
                        VALUES (@TranslationId, @BookId, @ChapterNumber, @VerseNumber, @Text)";

                    using var cmd = new SqlCommand(insertSql, connection, transaction);
                    cmd.Parameters.AddWithValue("@TranslationId", translationId);
                    cmd.Parameters.AddWithValue("@BookId", bookId);
                    cmd.Parameters.AddWithValue("@ChapterNumber", chapter);
                    cmd.Parameters.AddWithValue("@VerseNumber", verse);
                    cmd.Parameters.AddWithValue("@Text", text);

                    var rowsAffected = await cmd.ExecuteNonQueryAsync();
                    insertedCount += rowsAffected;
                }

                await transaction.CommitAsync();
                return insertedCount;
            }
            catch
            {
                await transaction.RollbackAsync();
                throw;
            }
        }

        /// <summary>
        /// Test database connection
        /// </summary>
        public async Task<bool> TestConnectionAsync()
        {
            try
            {
                using var connection = new SqlConnection(_connectionString);
                await connection.OpenAsync();
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Database connection test failed");
                return false;
            }
        }
    }
}