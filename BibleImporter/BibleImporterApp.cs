using Microsoft.Extensions.Logging;
using System.Text.Json;
using BibleImporter.Configuration;
using BibleImporter.Services;

namespace BibleImporter
{
    /// <summary>
    /// Main application class that orchestrates the Bible import process
    /// </summary>
    public class BibleImporterApp
    {
        private readonly ImporterConfig _config;
        private readonly BlobStorageService _blobService;
        private readonly XmlParsingService _xmlService;
        private readonly DatabaseService _dbService;
        private readonly ILogger<BibleImporterApp> _logger;

        public BibleImporterApp(
            ImporterConfig config,
            BlobStorageService blobService,
            XmlParsingService xmlService,
            DatabaseService dbService,
            ILogger<BibleImporterApp> logger)
        {
            _config = config;
            _blobService = blobService;
            _xmlService = xmlService;
            _dbService = dbService;
            _logger = logger;
        }

        /// <summary>
        /// Run the import application
        /// </summary>
        public async Task<int> RunAsync()
        {
            try
            {
                // Validate configuration
                if (!ValidateConfiguration())
                {
                    OutputError("Invalid configuration. Please check your config file.");
                    return 1;
                }

                // Test connections
                if (!await TestConnections())
                {
                    OutputError("Connection tests failed. Please check your configuration.");
                    return 1;
                }

                // Get user input for book name
                Console.Write("Enter the book name to import: ");
                var bookName = Console.ReadLine()?.Trim();

                if (string.IsNullOrWhiteSpace(bookName))
                {
                    OutputError("Book name cannot be empty.");
                    return 1;
                }

                // Execute the import process
                var result = await ImportBookAsync(bookName);
                
                // Output result in JSON format
                Console.WriteLine(JsonSerializer.Serialize(result));
                return result.ContainsKey("error") ? 1 : 0;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unhandled exception in application");
                OutputError($"Unexpected error: {ex.Message}");
                return 1;
            }
        }

        private bool ValidateConfiguration()
        {
            if (string.IsNullOrWhiteSpace(_config.AzureBlobConnectionString))
            {
                _logger.LogError("AzureBlobConnectionString is required");
                return false;
            }

            if (string.IsNullOrWhiteSpace(_config.BlobContainerName))
            {
                _logger.LogError("BlobContainerName is required");
                return false;
            }

            if (string.IsNullOrWhiteSpace(_config.SqlConnectionString))
            {
                _logger.LogError("SqlConnectionString is required");
                return false;
            }

            return true;
        }

        private async Task<bool> TestConnections()
        {
            try
            {
                // Test blob storage connection
                if (!await _blobService.TestConnectionAsync())
                {
                    _logger.LogError("Blob storage connection failed");
                    return false;
                }

                // Test database connection
                if (!await _dbService.TestConnectionAsync())
                {
                    _logger.LogError("Database connection failed");
                    return false;
                }

                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Connection test failed");
                return false;
            }
        }

        private async Task<Dictionary<string, object>> ImportBookAsync(string bookName)
        {
            try
            {
                // Step 1: Search and retrieve XML file from Azure Blob Storage
                _logger.LogInformation("Searching for XML file for book: {BookName}", bookName);
                var xmlContent = await _blobService.GetXmlFileByBookNameAsync(bookName);
                
                if (string.IsNullOrEmpty(xmlContent))
                {
                    return new Dictionary<string, object> 
                    { 
                        ["error"] = $"XML file not found for book: {bookName}" 
                    };
                }

                // Validate XML content retrieval
                if (xmlContent.Length < 100) // Basic sanity check
                {
                    return new Dictionary<string, object> 
                    { 
                        ["error"] = "Retrieved XML file appears to be invalid or empty" 
                    };
                }

                // Step 2: Parse XML content
                _logger.LogInformation("Parsing XML content for book: {BookName}", bookName);
                var parsedData = _xmlService.ParseUsfxXml(xmlContent, bookName.ToLower());
                
                if (!parsedData.Books.Any())
                {
                    return new Dictionary<string, object> 
                    { 
                        ["error"] = "No valid book data found in XML file" 
                    };
                }

                // Validate parsing result
                var totalVerses = parsedData.Books.Sum(b => b.Verses.Count);
                if (totalVerses == 0)
                {
                    return new Dictionary<string, object> 
                    { 
                        ["error"] = "No verses found in parsed XML data" 
                    };
                }

                // Step 3: Import data into database
                _logger.LogInformation("Importing data to database for {BookCount} books, {VerseCount} verses", 
                    parsedData.Books.Count, totalVerses);

                var result = await ImportToDatabase(parsedData);
                
                // Validate database import
                if (result.BooksImported == 0 || result.VersesImported == 0)
                {
                    return new Dictionary<string, object> 
                    { 
                        ["error"] = "Database import completed but no data was imported" 
                    };
                }

                return new Dictionary<string, object>
                {
                    ["books_copied"] = result.BooksImported,
                    ["verses_copied"] = result.VersesImported
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error importing book: {BookName}", bookName);
                return new Dictionary<string, object> 
                { 
                    ["error"] = $"Import failed: {ex.Message}" 
                };
            }
        }

        private async Task<ImportResult> ImportToDatabase(ParsedBibleData parsedData)
        {
            try
            {
                // Create or get translation
                var translationId = await _dbService.GetOrCreateTranslationAsync(
                    parsedData.Translation.Identifier,
                    parsedData.Translation.Name,
                    parsedData.Translation.LanguageCode,
                    parsedData.Translation.License);

                int totalBooksImported = 0;
                int totalVersesImported = 0;

                foreach (var book in parsedData.Books)
                {
                    // Create or get book
                    var bookId = await _dbService.GetOrCreateBookAsync(
                        book.Code,
                        book.Name,
                        book.Testament);

                    // Prepare verses for bulk insert
                    var verses = book.Verses.Select(v => (v.Chapter, v.Verse, v.Text)).ToList();
                    
                    if (verses.Any())
                    {
                        var versesImported = await _dbService.InsertVersesAsync(translationId, bookId, verses);
                        totalVersesImported += versesImported;
                        
                        if (versesImported > 0)
                        {
                            totalBooksImported++;
                        }
                    }
                }

                return new ImportResult
                {
                    BooksImported = totalBooksImported,
                    VersesImported = totalVersesImported
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Database import failed");
                throw new InvalidOperationException($"Database operation failed: {ex.Message}", ex);
            }
        }

        private void OutputError(string message)
        {
            var error = new { error = message };
            Console.WriteLine(JsonSerializer.Serialize(error));
        }

        private class ImportResult
        {
            public int BooksImported { get; set; }
            public int VersesImported { get; set; }
        }
    }
}