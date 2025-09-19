using System.Xml.Linq;
using System.Text.RegularExpressions;
using Microsoft.Extensions.Logging;
using BibleApi.Core;

namespace BibleImporter.Services
{
    /// <summary>
    /// Service for parsing USFX format XML files
    /// </summary>
    public class XmlParsingService
    {
        private readonly ILogger<XmlParsingService> _logger;

        public XmlParsingService(ILogger<XmlParsingService> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Parse USFX XML content and extract verses
        /// </summary>
        public ParsedBibleData ParseUsfxXml(string xmlContent, string identifier)
        {
            try
            {
                var doc = XDocument.Parse(xmlContent);
                var result = new ParsedBibleData();

                // Extract translation info
                result.Translation = ExtractTranslationInfo(doc, identifier);

                // Parse books and verses
                var books = doc.Descendants("book").ToList();
                foreach (var bookElement in books)
                {
                    var bookId = bookElement.Attribute("id")?.Value;
                    if (string.IsNullOrEmpty(bookId))
                        continue;

                    var bookData = ParseBook(bookElement, bookId);
                    if (bookData != null)
                    {
                        result.Books.Add(bookData);
                    }
                }

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to parse USFX XML");
                throw new InvalidOperationException($"XML parsing failed: {ex.Message}", ex);
            }
        }

        private TranslationInfo ExtractTranslationInfo(XDocument doc, string identifier)
        {
            // Default values
            var translation = new TranslationInfo
            {
                Identifier = identifier,
                Name = identifier.ToUpper(),
                LanguageCode = "en",
                License = "Public Domain"
            };

            // Try to extract from XML metadata if available
            var root = doc.Root;
            if (root != null)
            {
                // Look for common metadata patterns
                var titleElement = root.Descendants().FirstOrDefault(e => 
                    e.Name.LocalName.Equals("title", StringComparison.OrdinalIgnoreCase));
                if (titleElement != null && !string.IsNullOrWhiteSpace(titleElement.Value))
                {
                    translation.Name = titleElement.Value.Trim();
                }

                // Check for language indicators
                var langAttr = root.Attribute("lang");
                if (langAttr == null)
                {
                    // Try alternative attribute names
                    var xmlLangAttr = root.Attributes().FirstOrDefault(a => 
                        a.Name.LocalName == "lang" && a.Name.NamespaceName.Contains("xml"));
                    if (xmlLangAttr != null)
                    {
                        langAttr = xmlLangAttr;
                    }
                }
                
                if (langAttr != null && !string.IsNullOrWhiteSpace(langAttr.Value))
                {
                    translation.LanguageCode = langAttr.Value.Trim().Substring(0, Math.Min(2, langAttr.Value.Length));
                }
            }

            return translation;
        }

        private BookData? ParseBook(XElement bookElement, string bookId)
        {
            try
            {
                var bookCode = bookId.ToUpper();
                var bookName = BookMetadata.GetName(bookCode);
                
                var bookData = new BookData
                {
                    Code = bookCode,
                    Name = bookName,
                    Testament = DetermineTestament(bookCode)
                };

                var currentChapter = 1;
                var currentVerse = 1;

                foreach (var element in bookElement.Descendants())
                {
                    // Handle chapter markers
                    if (element.Name.LocalName == "c" || element.Name.LocalName == "chapter")
                    {
                        var chapterAttr = element.Attribute("id") ?? element.Attribute("n");
                        if (chapterAttr != null && int.TryParse(chapterAttr.Value, out int chapterNum))
                        {
                            currentChapter = chapterNum;
                            currentVerse = 1; // Reset verse counter for new chapter
                        }
                    }
                    // Handle verse markers and content
                    else if (element.Name.LocalName == "v" || element.Name.LocalName == "verse")
                    {
                        var verseAttr = element.Attribute("id") ?? element.Attribute("n");
                        if (verseAttr != null && int.TryParse(verseAttr.Value, out int verseNum))
                        {
                            currentVerse = verseNum;
                        }

                        // Get verse text - it might be in the element itself or following siblings
                        var verseText = ExtractVerseText(element);
                        if (!string.IsNullOrWhiteSpace(verseText))
                        {
                            bookData.Verses.Add(new VerseData
                            {
                                Chapter = (short)currentChapter,
                                Verse = (short)currentVerse,
                                Text = verseText.Trim()
                            });
                        }
                    }
                }

                return bookData.Verses.Any() ? bookData : null;
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to parse book {BookId}", bookId);
                return null;
            }
        }

        private string ExtractVerseText(XElement verseElement)
        {
            var text = new List<string>();

            // Get text from the verse element itself
            if (!string.IsNullOrWhiteSpace(verseElement.Value))
            {
                text.Add(verseElement.Value);
            }

            // Get text from following siblings until next verse marker
            var nextElement = verseElement.NextNode;
            while (nextElement != null)
            {
                if (nextElement is XElement elem)
                {
                    if (elem.Name.LocalName == "v" || elem.Name.LocalName == "verse" ||
                        elem.Name.LocalName == "c" || elem.Name.LocalName == "chapter")
                        break;
                    
                    if (!string.IsNullOrWhiteSpace(elem.Value))
                    {
                        text.Add(elem.Value);
                    }
                }
                else if (nextElement is XText textNode)
                {
                    if (!string.IsNullOrWhiteSpace(textNode.Value))
                    {
                        text.Add(textNode.Value);
                    }
                }

                nextElement = nextElement.NextNode;
            }

            // Clean up the text
            var result = string.Join(" ", text)
                .Trim()
                .Replace("\n", " ")
                .Replace("\r", " ");
            
            // Remove extra whitespace
            result = Regex.Replace(result, @"\s+", " ");

            return result;
        }

        private string? DetermineTestament(string bookCode)
        {
            if (BibleConstants.OldTestamentBooks.Contains(bookCode))
                return "OT";
            if (BibleConstants.NewTestamentBooks.Contains(bookCode))
                return "NT";
            return null;
        }
    }

    /// <summary>
    /// Container for parsed Bible data
    /// </summary>
    public class ParsedBibleData
    {
        public TranslationInfo Translation { get; set; } = new();
        public List<BookData> Books { get; set; } = new();
    }

    /// <summary>
    /// Translation information
    /// </summary>
    public class TranslationInfo
    {
        public string Identifier { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string LanguageCode { get; set; } = string.Empty;
        public string License { get; set; } = string.Empty;
    }

    /// <summary>
    /// Book data with verses
    /// </summary>
    public class BookData
    {
        public string Code { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string? Testament { get; set; }
        public List<VerseData> Verses { get; set; } = new();
    }

    /// <summary>
    /// Individual verse data
    /// </summary>
    public class VerseData
    {
        public short Chapter { get; set; }
        public short Verse { get; set; }
        public string Text { get; set; } = string.Empty;
    }
}