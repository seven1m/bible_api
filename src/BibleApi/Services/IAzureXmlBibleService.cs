using BibleApi.Models;

namespace BibleApi.Services
{
    /// <summary>
    /// Interface for Azure XML Bible Service
    /// </summary>
    public interface IAzureXmlBibleService
    {
        /// <summary>
        /// List all available Bible translations
        /// </summary>
        Task<List<Translation>> ListTranslationsAsync();

        /// <summary>
        /// Get translation metadata by identifier
        /// </summary>
        Task<Translation?> GetTranslationInfoAsync(string identifier);

        /// <summary>
        /// Get verses by book, chapter, and optional verse range
        /// </summary>
        Task<List<Verse>> GetVersesByReferenceAsync(string translationId, string book, int chapter, int? verseStart = null, int? verseEnd = null);

        /// <summary>
        /// Get all chapters for a specific book
        /// </summary>
        Task<List<BookChapter>> GetChaptersForBookAsync(string translationId, string bookId);

        /// <summary>
        /// Get a random verse from specified books
        /// </summary>
        Task<Verse?> GetRandomVerseAsync(string translationId, string[] books);
    }
}