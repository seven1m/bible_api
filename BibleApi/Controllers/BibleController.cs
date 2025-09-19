using Microsoft.AspNetCore.Mvc;
using BibleApi.Models;
using BibleApi.Services;
using BibleApi.Core;
using Microsoft.AspNetCore.Cors;

namespace BibleApi.Controllers
{
    /// <summary>
    /// Bible API controller (versioned) - equivalent to Python bible router
    /// </summary>
    [ApiController]
    [Route("v1")]
    [EnableCors]
    [Produces("application/json")]
    public class BibleController : ControllerBase
    {
        private readonly IAzureXmlBibleService _azureService;
        private readonly ILogger<BibleController> _logger;

        public BibleController(IAzureXmlBibleService azureService, ILogger<BibleController> logger)
        {
            _azureService = azureService;
            _logger = logger;
        }

        /// <summary>
        /// Helper method to get translation or use first available
        /// </summary>
        private async Task<Translation> GetTranslationAsync(string? identifier)
        {
            if (string.IsNullOrEmpty(identifier))
            {
                var translations = await _azureService.ListTranslationsAsync();
                if (translations.Any())
                {
                    identifier = translations.First().Identifier;
                }
                else
                {
                    throw new InvalidOperationException("No translations available");
                }
            }

            var translation = await _azureService.GetTranslationInfoAsync(identifier.ToLower());
            if (translation == null)
            {
                throw new KeyNotFoundException("Translation not found");
            }

            return translation;
        }

        /// <summary>
        /// List all available Bible translations
        /// GET /v1/data
        /// </summary>
        [HttpGet("data")]
        [ProducesResponseType(typeof(TranslationsResponse), 200)]
        public async Task<ActionResult<TranslationsResponse>> ListTranslations()
        {
            try
            {
                var baseUrl = $"{Request.Scheme}://{Request.Host}";
                var translations = await _azureService.ListTranslationsAsync();

                var translationsWithUrls = translations.Select(t => new TranslationWithUrl
                {
                    Identifier = t.Identifier,
                    Name = t.Name,
                    Language = t.Language,
                    LanguageCode = t.LanguageCode,
                    License = t.License,
                    Url = $"{baseUrl}/v1/data/{t.Identifier}"
                }).ToList();

                return Ok(new TranslationsResponse { Translations = translationsWithUrls });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error listing translations");
                return StatusCode(500, new { error = "Error listing translations" });
            }
        }

        /// <summary>
        /// Get books for a specific translation
        /// GET /v1/data/{translation_id}
        /// </summary>
        [HttpGet("data/{translationId}")]
        [ProducesResponseType(typeof(BooksResponse), 200)]
        [ProducesResponseType(404)]
        public async Task<ActionResult<BooksResponse>> GetTranslationBooks(string translationId)
        {
            try
            {
                var baseUrl = $"{Request.Scheme}://{Request.Host}";
                var translation = await GetTranslationAsync(translationId);

                // For now, return all Protestant books - in future this could be dynamic based on translation content
                var books = BibleConstants.ProtestantBooks.Select(bookId => new BookWithUrl
                {
                    Id = bookId,
                    Name = GetBookName(bookId),
                    Url = $"{baseUrl}/v1/data/{translation.Identifier}/{bookId}"
                }).ToList();

                return Ok(new BooksResponse 
                { 
                    Translation = translation, 
                    Books = books 
                });
            }
            catch (KeyNotFoundException)
            {
                return NotFound(new { error = "translation not found" });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting translation books for {TranslationId}", translationId);
                return StatusCode(500, new { error = "Error getting translation books" });
            }
        }

        /// <summary>
        /// Get chapters for a specific book in a translation
        /// GET /v1/data/{translation_id}/{book_id}
        /// </summary>
        [HttpGet("data/{translationId}/{bookId}")]
        [ProducesResponseType(typeof(ChaptersResponse), 200)]
        [ProducesResponseType(404)]
        public async Task<ActionResult<ChaptersResponse>> GetBookChapters(string translationId, string bookId)
        {
            try
            {
                var baseUrl = $"{Request.Scheme}://{Request.Host}";
                var translation = await GetTranslationAsync(translationId);
                var chapters = await _azureService.GetChaptersForBookAsync(translationId, bookId);

                if (!chapters.Any())
                {
                    return NotFound(new { error = "book not found" });
                }

                // Add URLs to chapters
                foreach (var chapter in chapters)
                {
                    chapter.Url = $"{baseUrl}/v1/data/{translation.Identifier}/{chapter.BookId}/{chapter.Chapter}";
                }

                return Ok(new ChaptersResponse 
                { 
                    Translation = translation, 
                    Chapters = chapters 
                });
            }
            catch (KeyNotFoundException)
            {
                return NotFound(new { error = "translation not found" });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting chapters for {TranslationId}/{BookId}", translationId, bookId);
                return StatusCode(500, new { error = "Error getting book chapters" });
            }
        }

        /// <summary>
        /// Get verses for a specific chapter
        /// GET /v1/data/{translation_id}/{book_id}/{chapter}
        /// </summary>
        [HttpGet("data/{translationId}/{bookId}/{chapter:int}")]
        [ProducesResponseType(typeof(VersesInChapterResponse), 200)]
        [ProducesResponseType(404)]
        public async Task<ActionResult<VersesInChapterResponse>> GetChapterVerses(string translationId, string bookId, int chapter)
        {
            try
            {
                var translation = await GetTranslationAsync(translationId);
                var verses = await _azureService.GetVersesByReferenceAsync(translationId, bookId, chapter);

                if (!verses.Any())
                {
                    return NotFound(new { error = "book/chapter not found" });
                }

                return Ok(new VersesInChapterResponse 
                { 
                    Translation = translation, 
                    Verses = verses 
                });
            }
            catch (KeyNotFoundException)
            {
                return NotFound(new { error = "translation not found" });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting verses for {TranslationId}/{BookId}/{Chapter}", translationId, bookId, chapter);
                return StatusCode(500, new { error = "Error getting chapter verses" });
            }
        }

        /// <summary>
        /// Get random verse from specified books
        /// GET /v1/data/{translation_id}/random/{book_id}
        /// </summary>
        [HttpGet("data/{translationId}/random/{bookId}")]
        [ProducesResponseType(typeof(RandomVerseResponse), 200)]
        [ProducesResponseType(404)]
        public async Task<ActionResult<RandomVerseResponse>> GetRandomVerseByBook(string translationId, string bookId)
        {
            try
            {
                var translation = await GetTranslationAsync(translationId);
                
                string[] books;
                var upperBookId = bookId.ToUpper();
                
                if (upperBookId == "OT")
                {
                    books = BibleConstants.OldTestamentBooks;
                }
                else if (upperBookId == "NT")
                {
                    books = BibleConstants.NewTestamentBooks;
                }
                else
                {
                    books = upperBookId.Split(',', StringSplitOptions.RemoveEmptyEntries);
                }

                var randomVerse = await _azureService.GetRandomVerseAsync(translation.Identifier, books);
                if (randomVerse == null)
                {
                    return NotFound(new { error = "error getting verse" });
                }

                return Ok(new RandomVerseResponse 
                { 
                    Translation = translation, 
                    RandomVerse = randomVerse 
                });
            }
            catch (KeyNotFoundException)
            {
                return NotFound(new { error = "translation not found" });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting random verse for {TranslationId}/{BookId}", translationId, bookId);
                return StatusCode(500, new { error = "Error getting random verse" });
            }
        }

        /// <summary>
        /// Helper method to get human-readable book names
        /// </summary>
        private static string GetBookName(string bookId)
        {
            var bookNames = new Dictionary<string, string>
            {
                {"GEN", "Genesis"}, {"EXO", "Exodus"}, {"LEV", "Leviticus"}, {"NUM", "Numbers"}, {"DEU", "Deuteronomy"},
                {"JOS", "Joshua"}, {"JDG", "Judges"}, {"RUT", "Ruth"}, {"1SA", "1 Samuel"}, {"2SA", "2 Samuel"},
                {"1KI", "1 Kings"}, {"2KI", "2 Kings"}, {"1CH", "1 Chronicles"}, {"2CH", "2 Chronicles"}, {"EZR", "Ezra"},
                {"NEH", "Nehemiah"}, {"EST", "Esther"}, {"JOB", "Job"}, {"PSA", "Psalms"}, {"PRO", "Proverbs"},
                {"ECC", "Ecclesiastes"}, {"SNG", "Song of Solomon"}, {"ISA", "Isaiah"}, {"JER", "Jeremiah"}, {"LAM", "Lamentations"},
                {"EZK", "Ezekiel"}, {"DAN", "Daniel"}, {"HOS", "Hosea"}, {"JOL", "Joel"}, {"AMO", "Amos"},
                {"OBA", "Obadiah"}, {"JON", "Jonah"}, {"MIC", "Micah"}, {"NAM", "Nahum"}, {"HAB", "Habakkuk"},
                {"ZEP", "Zephaniah"}, {"HAG", "Haggai"}, {"ZEC", "Zechariah"}, {"MAL", "Malachi"},
                {"MAT", "Matthew"}, {"MRK", "Mark"}, {"LUK", "Luke"}, {"JHN", "John"}, {"ACT", "Acts"},
                {"ROM", "Romans"}, {"1CO", "1 Corinthians"}, {"2CO", "2 Corinthians"}, {"GAL", "Galatians"}, {"EPH", "Ephesians"},
                {"PHP", "Philippians"}, {"COL", "Colossians"}, {"1TH", "1 Thessalonians"}, {"2TH", "2 Thessalonians"},
                {"1TI", "1 Timothy"}, {"2TI", "2 Timothy"}, {"TIT", "Titus"}, {"PHM", "Philemon"}, {"HEB", "Hebrews"},
                {"JAS", "James"}, {"1PE", "1 Peter"}, {"2PE", "2 Peter"}, {"1JN", "1 John"}, {"2JN", "2 John"},
                {"3JN", "3 John"}, {"JUD", "Jude"}, {"REV", "Revelation"}
            };

            return bookNames.TryGetValue(bookId, out string? name) ? name : bookId;
        }
    }
}