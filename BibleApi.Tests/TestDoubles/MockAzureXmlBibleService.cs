using BibleApi.Models;
using BibleApi.Services;
using BibleApi.Core;

namespace BibleApi.Tests.TestDoubles;

/// <summary>
/// Test double for IAzureXmlBibleService so unit tests don't hit Azure.
/// Moved from production project to keep runtime assembly lean.
/// </summary>
public class MockAzureXmlBibleService : IAzureXmlBibleService
{
    public Task<List<Translation>> ListTranslationsAsync() => Task.FromResult(new List<Translation>
    {
        new Translation { Identifier = "kjv", Name = "King James Version", Language = "english", LanguageCode = "en", License = "Public Domain" },
        new Translation { Identifier = "asv", Name = "American Standard Version", Language = "english", LanguageCode = "en", License = "Public Domain" }
    });

    public Task<Translation?> GetTranslationInfoAsync(string identifier) => Task.FromResult(
        new Translation { Identifier = identifier.ToLower(), Name = identifier.ToLower() == "asv" ? "American Standard Version" : "King James Version", Language = "english", LanguageCode = "en", License = "Public Domain" });

    public Task<List<Verse>> GetVersesByReferenceAsync(string translationId, string book, int chapter, int? verseStart = null, int? verseEnd = null)
    {
        var verses = new List<Verse>();
        var normalized = BookMetadata.Normalize(book);
        var name = BookMetadata.GetName(normalized);
        int start = verseStart ?? 1;
        int end = verseEnd ?? Math.Min(start + 3, 10);
        for (int v = start; v <= end; v++)
        {
            verses.Add(new Verse
            {
                BookId = normalized,
                Book = name,
                Chapter = chapter,
                VerseNumber = v,
                Text = $"Sample text {name} {chapter}:{v} ({translationId})"
            });
        }
        return Task.FromResult(verses);
    }

    public Task<List<BookChapter>> GetChaptersForBookAsync(string translationId, string bookId)
    {
        var normalized = BookMetadata.Normalize(bookId);
        var name = BookMetadata.GetName(normalized);
        var list = new List<BookChapter>();
        var count = Math.Min(BookMetadata.GetChapterCount(normalized), 5);
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
        var chapter = 1;
        var verse = 1;
        return Task.FromResult<Verse?>(new Verse { BookId = code, Book = name, Chapter = chapter, VerseNumber = verse, Text = $"Random {name} 1:1" });
    }
}
