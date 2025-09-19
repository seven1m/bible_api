using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace BibleImporter.Models
{
    /// <summary>
    /// Database model for Translation table matching SQL schema
    /// </summary>
    [Table("Translation", Schema = "dbo")]
    public class DbTranslation
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int TranslationId { get; set; }

        [Required]
        [StringLength(32)]
        public string Identifier { get; set; } = string.Empty;

        [Required]
        [StringLength(128)]
        public string Name { get; set; } = string.Empty;

        [Required]
        [StringLength(8)]
        public string LanguageCode { get; set; } = string.Empty;

        [StringLength(256)]
        public string? License { get; set; }

        [Required]
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    }

    /// <summary>
    /// Database model for Book table matching SQL schema
    /// </summary>
    [Table("Book", Schema = "dbo")]
    public class DbBook
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int BookId { get; set; }

        [Required]
        [StringLength(3)]
        public string Code { get; set; } = string.Empty;

        [Required]
        [StringLength(64)]
        public string Name { get; set; } = string.Empty;

        [StringLength(2)]
        public string? Testament { get; set; }
    }

    /// <summary>
    /// Database model for Verse table matching SQL schema
    /// </summary>
    [Table("Verse", Schema = "dbo")]
    public class DbVerse
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int VerseId { get; set; }

        [Required]
        public int TranslationId { get; set; }

        [Required]
        public int BookId { get; set; }

        [Required]
        public short ChapterNumber { get; set; }

        [Required]
        public short VerseNumber { get; set; }

        [Required]
        public string Text { get; set; } = string.Empty;

        // Navigation properties
        [ForeignKey("TranslationId")]
        public virtual DbTranslation Translation { get; set; } = null!;

        [ForeignKey("BookId")]
        public virtual DbBook Book { get; set; } = null!;
    }
}