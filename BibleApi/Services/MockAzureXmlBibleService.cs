using BibleApi.Models;
using BibleApi.Core;

namespace BibleApi.Services
{
    /// <summary>
    /// Mock implementation for testing without Azure connection
    /// </summary>
    public class MockAzureXmlBibleService : IAzureXmlBibleService
    {
        public Task<List<Translation>> ListTranslationsAsync()
        {
            var translations = new List<Translation>
            {
                new Translation
                {
                    Identifier = "kjv",
                    Name = "King James Version",
                    Language = "english",
                    LanguageCode = "en",
                    License = "Public Domain"
                },
                new Translation
                {
                    Identifier = "asv",
                    Name = "American Standard Version",
                    Language = "english",
                    LanguageCode = "en",
                    License = "Public Domain"
                }
            };
            
            return Task.FromResult(translations);
        }

        public Task<Translation?> GetTranslationInfoAsync(string identifier)
        {
            var translations = new List<Translation>
            {
                new Translation
                {
                    Identifier = "kjv",
                    Name = "King James Version",
                    Language = "english",
                    LanguageCode = "en",
                    License = "Public Domain"
                },
                new Translation
                {
                    Identifier = "asv",
                    Name = "American Standard Version", 
                    Language = "english",
                    LanguageCode = "en",
                    License = "Public Domain"
                }
            };

            var translation = translations.FirstOrDefault(t => t.Identifier == identifier.ToLower());
            return Task.FromResult(translation);
        }

        public Task<List<Verse>> GetVersesByReferenceAsync(string translationId, string book, int chapter, int? verseStart = null, int? verseEnd = null)
        {
            var verses = new List<Verse>();
            var startVerse = verseStart ?? 1;
            var endVerse = verseEnd ?? Math.Min(startVerse + 5, 31);

            var normalizedBook = BookMetadata.Normalize(book);
            var bookName = BookMetadata.GetName(normalizedBook);

            for (int v = startVerse; v <= endVerse; v++)
            {
                verses.Add(new Verse
                {
                    BookId = normalizedBook,
                    Book = bookName,
                    Chapter = chapter,
                    VerseNumber = v,
                    Text = $"For God so loved the world, that he gave his only begotten Son... ({bookName} {chapter}:{v})"
                });
            }

            return Task.FromResult(verses);
        }

        public Task<List<BookChapter>> GetChaptersForBookAsync(string translationId, string bookId)
        {
            var chapters = new List<BookChapter>();
            var normalizedBook = BookMetadata.Normalize(bookId);
            var bookName = BookMetadata.GetName(normalizedBook);
            var chapterCount = BookMetadata.GetChapterCount(normalizedBook);

            for (int i = 1; i <= Math.Min(chapterCount, 5); i++) // Limit for demo
            {
                chapters.Add(new BookChapter
                {
                    BookId = normalizedBook,
                    Book = bookName,
                    Chapter = i
                });
            }

            return Task.FromResult(chapters);
        }

        public Task<Verse?> GetRandomVerseAsync(string translationId, string[] books)
        {
            var random = new Random();
            var randomBook = books[random.Next(books.Length)];
            var normalizedBook = BookMetadata.Normalize(randomBook);
            var bookName = BookMetadata.GetName(normalizedBook);
            var randomChapter = random.Next(1, BookMetadata.GetChapterCount(normalizedBook) + 1);
            var randomVerse = random.Next(1, 21);

            var verse = new Verse
            {
                BookId = normalizedBook,
                Book = bookName,
                Chapter = randomChapter,
                VerseNumber = randomVerse,
                Text = $"For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life. ({bookName} {randomChapter}:{randomVerse})"
            };

            return Task.FromResult<Verse?>(verse);
        }

    // Uses centralized BookMetadata for names, chapter counts, normalization.
    }
}