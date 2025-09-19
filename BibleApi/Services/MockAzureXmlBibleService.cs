using BibleApi.Models;

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

            for (int v = startVerse; v <= endVerse; v++)
            {
                verses.Add(new Verse
                {
                    BookId = book.ToUpper(),
                    Book = GetBookName(book.ToUpper()),
                    Chapter = chapter,
                    VerseNumber = v,
                    Text = $"For God so loved the world, that he gave his only begotten Son... ({GetBookName(book.ToUpper())} {chapter}:{v})"
                });
            }

            return Task.FromResult(verses);
        }

        public Task<List<BookChapter>> GetChaptersForBookAsync(string translationId, string bookId)
        {
            var chapters = new List<BookChapter>();
            var chapterCount = GetDefaultChapterCount(bookId.ToUpper());

            for (int i = 1; i <= Math.Min(chapterCount, 5); i++) // Limit for demo
            {
                chapters.Add(new BookChapter
                {
                    BookId = bookId.ToUpper(),
                    Book = GetBookName(bookId.ToUpper()),
                    Chapter = i
                });
            }

            return Task.FromResult(chapters);
        }

        public Task<Verse?> GetRandomVerseAsync(string translationId, string[] books)
        {
            var random = new Random();
            var randomBook = books[random.Next(books.Length)];
            var randomChapter = random.Next(1, 11);
            var randomVerse = random.Next(1, 21);

            var verse = new Verse
            {
                BookId = randomBook.ToUpper(),
                Book = GetBookName(randomBook.ToUpper()),
                Chapter = randomChapter,
                VerseNumber = randomVerse,
                Text = $"For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life. ({GetBookName(randomBook.ToUpper())} {randomChapter}:{randomVerse})"
            };

            return Task.FromResult<Verse?>(verse);
        }

        private static string GetBookName(string bookId)
        {
            var bookNames = new Dictionary<string, string>
            {
                {"GEN", "Genesis"}, {"EXO", "Exodus"}, {"MAT", "Matthew"}, {"MRK", "Mark"}, 
                {"LUK", "Luke"}, {"JHN", "John"}, {"ACT", "Acts"}, {"ROM", "Romans"},
                {"1CO", "1 Corinthians"}, {"REV", "Revelation"}
            };

            return bookNames.TryGetValue(bookId, out string? name) ? name : bookId;
        }

        private static int GetDefaultChapterCount(string bookId)
        {
            var chapterCounts = new Dictionary<string, int>
            {
                {"GEN", 50}, {"EXO", 40}, {"MAT", 28}, {"MRK", 16}, 
                {"LUK", 24}, {"JHN", 21}, {"ACT", 28}, {"ROM", 16},
                {"1CO", 16}, {"REV", 22}
            };

            return chapterCounts.TryGetValue(bookId, out int count) ? count : 25;
        }
    }
}