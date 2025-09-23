using BibleApi.Models;
using BibleApi.Core;

namespace BibleApi.Services;

/// <summary>
/// Development mock service for testing without Azure Storage.
/// Used when Azure configuration is missing in development mode.
/// </summary>
public class MockAzureXmlBibleService : IAzureXmlBibleService
{
    public Task<List<Translation>> ListTranslationsAsync() => Task.FromResult(new List<Translation>
    {
        new Translation { Identifier = "kjv", Name = "King James Version", Language = "english", LanguageCode = "en", License = "Public Domain" },
        new Translation { Identifier = "asv", Name = "American Standard Version", Language = "english", LanguageCode = "en", License = "Public Domain" },
        new Translation { Identifier = "web", Name = "World English Bible", Language = "english", LanguageCode = "en", License = "Public Domain" }
    });

    public Task<Translation?> GetTranslationInfoAsync(string identifier) => Task.FromResult<Translation?>(
        identifier.ToLower() switch
        {
            "kjv" => new Translation { Identifier = "kjv", Name = "King James Version", Language = "english", LanguageCode = "en", License = "Public Domain" },
            "asv" => new Translation { Identifier = "asv", Name = "American Standard Version", Language = "english", LanguageCode = "en", License = "Public Domain" },
            "web" => new Translation { Identifier = "web", Name = "World English Bible", Language = "english", LanguageCode = "en", License = "Public Domain" },
            _ => new Translation { Identifier = identifier, Name = $"Mock Translation ({identifier})", Language = "english", LanguageCode = "en", License = "Public Domain" }
        });

    public Task<List<Verse>> GetVersesByReferenceAsync(string translationId, string book, int chapter, int? verseStart = null, int? verseEnd = null)
    {
        var verses = new List<Verse>();
        var normalized = BookMetadata.Normalize(book);
        
        // Validate book - return empty if invalid
        if (string.IsNullOrEmpty(normalized) || !BookMetadata.IsValid(normalized))
        {
            return Task.FromResult(verses);
        }
        
        var name = BookMetadata.GetName(normalized);
        int start = verseStart ?? 1;
        int end = verseEnd ?? Math.Min(start + 2, 10); // Default to 3 verses if no end specified
        
        for (int v = start; v <= end; v++)
        {
            verses.Add(new Verse
            {
                BookId = normalized,
                Book = name,
                Chapter = chapter,
                VerseNumber = v,
                Text = $"This is sample verse text for {name} {chapter}:{v} from the {translationId.ToUpper()} translation. This is mock data for development purposes."
            });
        }
        return Task.FromResult(verses);
    }

    public Task<List<BookChapter>> GetChaptersForBookAsync(string translationId, string bookId)
    {
        var normalized = BookMetadata.Normalize(bookId);
        var list = new List<BookChapter>();
        
        // Validate book - return empty if invalid
        if (string.IsNullOrEmpty(normalized) || !BookMetadata.IsValid(normalized))
        {
            return Task.FromResult(list);
        }
        
        var name = BookMetadata.GetName(normalized);
        var count = Math.Min(BookMetadata.GetChapterCount(normalized), 5); // Limit for demo
        for (int i = 1; i <= count; i++)
        {
            list.Add(new BookChapter { BookId = normalized, Book = name, Chapter = i });
        }
        return Task.FromResult(list);
    }

    public Task<Verse?> GetRandomVerseAsync(string translationId, string[] books)
    {
        if (books.Length == 0) return Task.FromResult<Verse?>(null);
        
        var r = new Random();
        var pick = books[r.Next(books.Length)];
        var code = BookMetadata.Normalize(pick);
        var name = BookMetadata.GetName(code);
        
        if (string.IsNullOrEmpty(code))
        {
            return Task.FromResult<Verse?>(null);
        }
        
        var chapter = r.Next(1, Math.Min(BookMetadata.GetChapterCount(code), 10) + 1);
        var verse = r.Next(1, 32); // Reasonable verse range
        
        return Task.FromResult<Verse?>(new Verse 
        { 
            BookId = code, 
            Book = name, 
            Chapter = chapter, 
            VerseNumber = verse, 
            Text = $"This is a random verse from {name} {chapter}:{verse} in the {translationId.ToUpper()} translation. This is mock data for development." 
        });
    }
}