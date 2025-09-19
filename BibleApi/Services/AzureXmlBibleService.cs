using Azure.Storage.Blobs;
using Azure.Core;
using System.Xml.Linq;
using System.Text.RegularExpressions;
using BibleApi.Models;
using BibleApi.Configuration;
using BibleApi.Core;
using Microsoft.Extensions.Options;
using Microsoft.Extensions.Logging;

namespace BibleApi.Services
{
    /// <summary>
    /// Service to read Bible data directly from XML files in Azure Blob Storage (equivalent to Python AzureXMLBibleService)
    /// </summary>
    public class AzureXmlBibleService : IAzureXmlBibleService
    {
        private readonly BlobServiceClient _blobServiceClient;
        private readonly BlobContainerClient _containerClient;
        private readonly AppSettings _settings;
        private readonly ILogger<AzureXmlBibleService> _logger;

        // Cache for parsed XML data to avoid re-parsing
        private readonly Dictionary<string, string> _xmlCache = new();
        private readonly Dictionary<string, Translation> _translationCache = new();
        private List<Translation>? _availableTranslations;

        public AzureXmlBibleService(IOptions<AppSettings> settings, ILogger<AzureXmlBibleService> logger)
        {
            _settings = settings.Value;
            _logger = logger;

            if (string.IsNullOrEmpty(_settings.AzureStorageConnectionString))
            {
                throw new InvalidOperationException("AZURE_STORAGE_CONNECTION_STRING is required");
            }

            try
            {
                _blobServiceClient = new BlobServiceClient(_settings.AzureStorageConnectionString);
                _containerClient = _blobServiceClient.GetBlobContainerClient(_settings.AzureContainerName);
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Failed to connect to Azure Blob Storage: {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Get XML content from Azure blob with caching
        /// </summary>
        private async Task<string?> GetXmlContentAsync(string filePath)
        {
            if (_xmlCache.TryGetValue(filePath, out string? cached))
            {
                return cached;
            }

            try
            {
                var blobClient = _containerClient.GetBlobClient(filePath);
                var response = await blobClient.DownloadContentAsync();
                var content = response.Value.Content.ToString();
                _xmlCache[filePath] = content;
                return content;
            }
            catch (Azure.RequestFailedException ex) when (ex.Status == 404)
            {
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error reading {FilePath}", filePath);
                return null;
            }
        }

        /// <summary>
        /// Extract translation metadata from XML
        /// </summary>
        private Translation ParseXmlForTranslationInfo(string xmlContent, string identifier)
        {
            try
            {
                var doc = XDocument.Parse(xmlContent);
                var root = doc.Root;

                // Default values
                string name = identifier.ToUpper();
                string license = "Public Domain";
                string language = "english";
                string languageCode = "en";

                if (root != null)
                {
                    // Check for OSIS format
                    var osisNamespace = XNamespace.Get("http://www.bibletechnologies.net/2003/OSIS/namespace");
                    if (root.Name.LocalName == "osis")
                    {
                        var work = root.Descendants(osisNamespace + "work").FirstOrDefault();
                        if (work != null)
                        {
                            var titleElem = work.Descendants(osisNamespace + "title").FirstOrDefault();
                            if (titleElem != null && !string.IsNullOrEmpty(titleElem.Value))
                            {
                                name = titleElem.Value;
                            }

                            var rightsElem = work.Descendants(osisNamespace + "rights").FirstOrDefault();
                            if (rightsElem != null && !string.IsNullOrEmpty(rightsElem.Value))
                            {
                                license = rightsElem.Value;
                            }
                        }
                    }
                    // Check for other XML formats
                    else if (root.Attribute("title") != null)
                    {
                        name = root.Attribute("title")?.Value ?? name;
                    }
                    else if (root.Attribute("name") != null)
                    {
                        name = root.Attribute("name")?.Value ?? name;
                    }
                }

                // Determine language from identifier
                if (identifier.ToLower().Contains("romanian") || identifier.ToLower().Contains("ro-"))
                {
                    language = "romanian";
                    languageCode = "ro";
                }

                return new Translation
                {
                    Identifier = identifier,
                    Name = name,
                    Language = language,
                    LanguageCode = languageCode,
                    License = license
                };
            }
            catch (System.Xml.XmlException)
            {
                // Return basic info if XML parsing fails
                return new Translation
                {
                    Identifier = identifier,
                    Name = identifier.ToUpper(),
                    Language = identifier.ToLower().Contains("romanian") ? "romanian" : "english",
                    LanguageCode = identifier.ToLower().Contains("romanian") ? "ro" : "en",
                    License = "Unknown"
                };
            }
        }

        /// <summary>
        /// List all available Bible translations from container
        /// </summary>
        public async Task<List<Translation>> ListTranslationsAsync()
        {
            if (_availableTranslations != null)
            {
                return _availableTranslations;
            }

            var translations = new List<Translation>();

            try
            {
                await foreach (var blob in _containerClient.GetBlobsAsync())
                {
                    if (blob.Name.EndsWith(".xml", StringComparison.OrdinalIgnoreCase))
                    {
                        // Extract identifier from filename
                        var filename = blob.Name.Contains('/') 
                            ? blob.Name.Split('/').Last() 
                            : blob.Name;
                        
                        var identifier = Path.GetFileNameWithoutExtension(filename).ToLower();

                        // Get translation info by parsing XML
                        var xmlContent = await GetXmlContentAsync(blob.Name);
                        if (!string.IsNullOrEmpty(xmlContent))
                        {
                            var translation = ParseXmlForTranslationInfo(xmlContent, identifier);
                            translations.Add(translation);

                            // Cache the translation info with file path
                            _translationCache[identifier] = translation;
                        }
                    }
                }

                _availableTranslations = translations;
                return translations;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error listing translations");
                return new List<Translation>();
            }
        }

        /// <summary>
        /// Get translation metadata by identifier
        /// </summary>
        public async Task<Translation?> GetTranslationInfoAsync(string identifier)
        {
            var normalizedId = identifier.ToLower();

            if (_translationCache.TryGetValue(normalizedId, out Translation? cached))
            {
                return cached;
            }

            // Refresh translations list if not cached
            var translations = await ListTranslationsAsync();

            return translations.FirstOrDefault(t => t.Identifier == normalizedId);
        }

    // Book metadata normalization provided by BookMetadata.Normalize

        /// <summary>
        /// Get verses by book, chapter, and optional verse range
        /// </summary>
        public async Task<List<Verse>> GetVersesByReferenceAsync(string translationId, string book, int chapter, int? verseStart = null, int? verseEnd = null)
        {
            var translation = await GetTranslationInfoAsync(translationId);
            if (translation == null)
                return new List<Verse>();

            // For now, return a simple implementation - in real scenario this would parse XML
            // This is a minimal placeholder to allow the API to work
            var verses = new List<Verse>();
            
            var normalizedBook = BookMetadata.Normalize(book);
            var bookName = BookMetadata.GetName(normalizedBook);
            
            // Create some sample verses for demonstration
            var startVerse = verseStart ?? 1;
            var endVerse = verseEnd ?? Math.Min(startVerse + 10, 31); // Limit to reasonable range
            
            for (int v = startVerse; v <= endVerse; v++)
            {
                verses.Add(new Verse
                {
                    BookId = normalizedBook,
                    Book = bookName,
                    Chapter = chapter,
                    VerseNumber = v,
                    Text = $"Sample verse text for {bookName} {chapter}:{v} from {translation.Name}"
                });
            }
            
            return verses;
        }

        /// <summary>
        /// Get all chapters for a specific book
        /// </summary>
        public async Task<List<BookChapter>> GetChaptersForBookAsync(string translationId, string bookId)
        {
            var translation = await GetTranslationInfoAsync(translationId);
            if (translation == null)
                return new List<BookChapter>();

            // For now, return a simple implementation
            var normalizedBook = BookMetadata.Normalize(bookId);
            var bookName = BookMetadata.GetName(normalizedBook);
            var chapters = new List<BookChapter>();
            
            // Most books have reasonable chapter counts - this is a placeholder
            var chapterCount = BookMetadata.GetChapterCount(normalizedBook);
            
            for (int i = 1; i <= chapterCount; i++)
            {
                chapters.Add(new BookChapter
                {
                    BookId = normalizedBook,
                    Book = bookName,
                    Chapter = i
                });
            }
            
            return chapters;
        }

        /// <summary>
        /// Get a random verse from specified books
        /// </summary>
        public async Task<Verse?> GetRandomVerseAsync(string translationId, string[] books)
        {
            var translation = await GetTranslationInfoAsync(translationId);
            if (translation == null || !books.Any())
                return null;

            // Simple random implementation
            var random = new Random();
            var randomBook = books[random.Next(books.Length)];
            var normalizedBook = BookMetadata.Normalize(randomBook);
            var bookName = BookMetadata.GetName(normalizedBook);
            
            var randomChapter = random.Next(1, BookMetadata.GetChapterCount(normalizedBook) + 1);
            var randomVerse = random.Next(1, 32); // Most chapters don't exceed 31 verses
            
            return new Verse
            {
                BookId = normalizedBook,
                Book = bookName,
                Chapter = randomChapter,
                VerseNumber = randomVerse,
                Text = $"Random verse text for {bookName} {randomChapter}:{randomVerse} from {translation.Name}"
            };
        }

    // Book name lookup provided by BookMetadata.GetName

    // Chapter counts provided by BookMetadata.GetChapterCount
    }
}