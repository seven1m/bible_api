using System.ComponentModel.DataAnnotations;

namespace BibleApi.Models
{
    /// <summary>
    /// Represents a Bible translation (equivalent to Python Translation schema)
    /// </summary>
    public class Translation
    {
        [Required]
        public string Identifier { get; set; } = string.Empty;
        
        [Required]
        public string Name { get; set; } = string.Empty;
        
        [Required]
        public string Language { get; set; } = string.Empty;
        
        [Required]
        public string LanguageCode { get; set; } = string.Empty;
        
        [Required]
        public string License { get; set; } = string.Empty;
    }

    /// <summary>
    /// Represents a single Bible verse (equivalent to Python Verse schema)
    /// </summary>
    public class Verse
    {
        [Required]
        public string BookId { get; set; } = string.Empty;
        
        [Required]
        public string Book { get; set; } = string.Empty;
        
        [Required]
        public int Chapter { get; set; }
        
        [Required]
        public int VerseNumber { get; set; }
        
        [Required]
        public string Text { get; set; } = string.Empty;
    }

    /// <summary>
    /// Response model for verse queries (equivalent to Python VerseResponse schema)
    /// </summary>
    public class VerseResponse
    {
        [Required]
        public string Reference { get; set; } = string.Empty;
        
        [Required]
        public List<Verse> Verses { get; set; } = new();
        
        [Required]
        public string Text { get; set; } = string.Empty;
        
        [Required]
        public string TranslationId { get; set; } = string.Empty;
        
        [Required]
        public string TranslationName { get; set; } = string.Empty;
        
        [Required]
        public string TranslationNote { get; set; } = string.Empty;
    }

    /// <summary>
    /// Represents a book chapter reference (equivalent to Python BookChapter schema)
    /// </summary>
    public class BookChapter
    {
        [Required]
        public string BookId { get; set; } = string.Empty;
        
        [Required]
        public string Book { get; set; } = string.Empty;
        
        [Required]
        public int Chapter { get; set; }
        
        public string? Url { get; set; }
    }

    /// <summary>
    /// Response model for chapters queries (equivalent to Python ChaptersResponse schema)
    /// </summary>
    public class ChaptersResponse
    {
        [Required]
        public Translation Translation { get; set; } = new();
        
        [Required]
        public List<BookChapter> Chapters { get; set; } = new();
    }

    /// <summary>
    /// Response model for verses in a chapter (equivalent to Python VersesInChapterResponse schema)
    /// </summary>
    public class VersesInChapterResponse
    {
        [Required]
        public Translation Translation { get; set; } = new();
        
        [Required]
        public List<Verse> Verses { get; set; } = new();
    }

    /// <summary>
    /// Response model for random verse queries (equivalent to Python RandomVerseResponse schema)
    /// </summary>
    public class RandomVerseResponse
    {
        [Required]
        public Translation Translation { get; set; } = new();
        
        [Required]
        public Verse RandomVerse { get; set; } = new();
    }

    /// <summary>
    /// Response model for translation listings
    /// </summary>
    public class TranslationsResponse
    {
        [Required]
        public List<TranslationWithUrl> Translations { get; set; } = new();
    }

    /// <summary>
    /// Translation with URL for API navigation
    /// </summary>
    public class TranslationWithUrl : Translation
    {
        public string? Url { get; set; }
    }

    /// <summary>
    /// Response model for book listings
    /// </summary>
    public class BooksResponse
    {
        [Required]
        public Translation Translation { get; set; } = new();
        
        [Required]
        public List<BookWithUrl> Books { get; set; } = new();
    }

    /// <summary>
    /// Book with URL for API navigation
    /// </summary>
    public class BookWithUrl
    {
        [Required]
        public string Id { get; set; } = string.Empty;
        
        [Required]
        public string Name { get; set; } = string.Empty;
        
        public string? Url { get; set; }
    }
}