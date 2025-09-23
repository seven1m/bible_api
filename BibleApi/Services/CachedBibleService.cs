using Microsoft.Extensions.Caching.Memory;
using BibleApi.Models;

namespace BibleApi.Services;

/// <summary>
/// Cached wrapper around Bible service for improved performance.
/// Caches frequently accessed data like translations and verses.
/// </summary>
public class CachedBibleService : IAzureXmlBibleService
{
    private readonly IAzureXmlBibleService _innerService;
    private readonly IMemoryCache _cache;
    private readonly ILogger<CachedBibleService> _logger;

    // Cache configuration
    private readonly TimeSpan _translationsCacheExpiry = TimeSpan.FromHours(1);
    private readonly TimeSpan _versesCacheExpiry = TimeSpan.FromMinutes(30);
    private readonly TimeSpan _chaptersCacheExpiry = TimeSpan.FromMinutes(15);

    public CachedBibleService(
        IAzureXmlBibleService innerService,
        IMemoryCache cache,
        ILogger<CachedBibleService> logger)
    {
        _innerService = innerService;
        _cache = cache;
        _logger = logger;
    }

    public async Task<List<Translation>> ListTranslationsAsync()
    {
        const string cacheKey = "translations_list";
        
        if (_cache.TryGetValue(cacheKey, out List<Translation>? cached))
        {
            _logger.LogDebug("Retrieved {Count} translations from cache", cached?.Count ?? 0);
            return cached ?? new List<Translation>();
        }

        var translations = await _innerService.ListTranslationsAsync();
        
        var cacheOptions = new MemoryCacheEntryOptions
        {
            AbsoluteExpirationRelativeToNow = _translationsCacheExpiry,
            SlidingExpiration = TimeSpan.FromMinutes(15),
            Priority = CacheItemPriority.High
        };

        _cache.Set(cacheKey, translations, cacheOptions);
        _logger.LogDebug("Cached {Count} translations for {Expiry}", translations.Count, _translationsCacheExpiry);
        
        return translations;
    }

    public async Task<Translation?> GetTranslationInfoAsync(string identifier)
    {
        var cacheKey = $"translation_{identifier.ToLower()}";
        
        if (_cache.TryGetValue(cacheKey, out Translation? cached))
        {
            _logger.LogDebug("Retrieved translation {Identifier} from cache", identifier);
            return cached;
        }

        var translation = await _innerService.GetTranslationInfoAsync(identifier);
        
        if (translation != null)
        {
            var cacheOptions = new MemoryCacheEntryOptions
            {
                AbsoluteExpirationRelativeToNow = _translationsCacheExpiry,
                SlidingExpiration = TimeSpan.FromMinutes(10),
                Priority = CacheItemPriority.Normal
            };

            _cache.Set(cacheKey, translation, cacheOptions);
            _logger.LogDebug("Cached translation {Identifier}", identifier);
        }
        
        return translation;
    }

    public async Task<List<Verse>> GetVersesByReferenceAsync(string translationId, string book, int chapter, int? verseStart = null, int? verseEnd = null)
    {
        var cacheKey = $"verses_{translationId}_{book}_{chapter}_{verseStart}_{verseEnd}".ToLower();
        
        if (_cache.TryGetValue(cacheKey, out List<Verse>? cached))
        {
            _logger.LogDebug("Retrieved {Count} verses from cache for {Translation}/{Book}/{Chapter}", 
                cached?.Count ?? 0, translationId, book, chapter);
            return cached ?? new List<Verse>();
        }

        var verses = await _innerService.GetVersesByReferenceAsync(translationId, book, chapter, verseStart, verseEnd);
        
        var cacheOptions = new MemoryCacheEntryOptions
        {
            AbsoluteExpirationRelativeToNow = _versesCacheExpiry,
            SlidingExpiration = TimeSpan.FromMinutes(10),
            Priority = CacheItemPriority.Normal
        };

        _cache.Set(cacheKey, verses, cacheOptions);
        _logger.LogDebug("Cached {Count} verses for {Translation}/{Book}/{Chapter}", 
            verses.Count, translationId, book, chapter);
        
        return verses;
    }

    public async Task<List<BookChapter>> GetChaptersForBookAsync(string translationId, string bookId)
    {
        var cacheKey = $"chapters_{translationId}_{bookId}".ToLower();
        
        if (_cache.TryGetValue(cacheKey, out List<BookChapter>? cached))
        {
            _logger.LogDebug("Retrieved {Count} chapters from cache for {Translation}/{Book}", 
                cached?.Count ?? 0, translationId, bookId);
            return cached ?? new List<BookChapter>();
        }

        var chapters = await _innerService.GetChaptersForBookAsync(translationId, bookId);
        
        var cacheOptions = new MemoryCacheEntryOptions
        {
            AbsoluteExpirationRelativeToNow = _chaptersCacheExpiry,
            SlidingExpiration = TimeSpan.FromMinutes(5),
            Priority = CacheItemPriority.Normal
        };

        _cache.Set(cacheKey, chapters, cacheOptions);
        _logger.LogDebug("Cached {Count} chapters for {Translation}/{Book}", 
            chapters.Count, translationId, bookId);
        
        return chapters;
    }

    public async Task<Verse?> GetRandomVerseAsync(string translationId, string[] books)
    {
        // Don't cache random verses as they should be different each time
        return await _innerService.GetRandomVerseAsync(translationId, books);
    }
}