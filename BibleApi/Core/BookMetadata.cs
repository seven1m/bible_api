using System.Text.RegularExpressions;

namespace BibleApi.Core
{
    /// <summary>
    /// Centralized metadata for Bible book names, chapter counts, and normalization utilities.
    /// Replaces duplicated dictionaries and helpers across services and controller.
    /// </summary>
    public static class BookMetadata
    {
        private static readonly Dictionary<string, string> _bookNames = new(StringComparer.OrdinalIgnoreCase)
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

        private static readonly Dictionary<string, int> _chapterCounts = new(StringComparer.OrdinalIgnoreCase)
        {
            {"GEN", 50}, {"EXO", 40}, {"LEV", 27}, {"NUM", 36}, {"DEU", 34},
            {"JOS", 24}, {"JDG", 21}, {"RUT", 4}, {"1SA", 31}, {"2SA", 24},
            {"1KI", 22}, {"2KI", 25}, {"1CH", 29}, {"2CH", 36}, {"EZR", 10},
            {"NEH", 13}, {"EST", 10}, {"JOB", 42}, {"PSA", 150}, {"PRO", 31},
            {"ECC", 12}, {"SNG", 8}, {"ISA", 66}, {"JER", 52}, {"LAM", 5},
            {"EZK", 48}, {"DAN", 12}, {"HOS", 14}, {"JOL", 3}, {"AMO", 9},
            {"OBA", 1}, {"JON", 4}, {"MIC", 7}, {"NAM", 3}, {"HAB", 3},
            {"ZEP", 3}, {"HAG", 2}, {"ZEC", 14}, {"MAL", 4},
            {"MAT", 28}, {"MRK", 16}, {"LUK", 24}, {"JHN", 21}, {"ACT", 28},
            {"ROM", 16}, {"1CO", 16}, {"2CO", 13}, {"GAL", 6}, {"EPH", 6},
            {"PHP", 4}, {"COL", 4}, {"1TH", 5}, {"2TH", 3}, {"1TI", 6}, {"2TI", 4},
            {"TIT", 3}, {"PHM", 1}, {"HEB", 13}, {"JAS", 5}, {"1PE", 5}, {"2PE", 3}, {"1JN", 5}, {"2JN", 1}, {"3JN", 1}, {"JUD", 1}, {"REV", 22}
        };

        private static readonly Dictionary<string, string> _nameToCode = new(StringComparer.OrdinalIgnoreCase);

        static BookMetadata()
        {
            // Build reverse lookup (remove spaces/punctuation for normalization keys)
            foreach (var kvp in _bookNames)
            {
                var normalized = Regex.Replace(kvp.Value, "[^A-Za-z0-9]", "");
                if (!_nameToCode.ContainsKey(normalized))
                    _nameToCode[normalized] = kvp.Key;
            }
        }

        /// <summary>
        /// Normalize user-provided book input to a canonical 3+ character code.
        /// </summary>
        public static string Normalize(string input)
        {
            if (string.IsNullOrWhiteSpace(input)) return string.Empty;
            var raw = input.Trim().ToUpper();
            if (_bookNames.ContainsKey(raw)) return raw; // already a code

            var condensed = Regex.Replace(raw, "[^A-Z0-9]", "");
            if (_nameToCode.TryGetValue(condensed, out var code)) return code;

            // Handle numbers at start like 1SAMUEL / 2KINGS already condensed
            if (_nameToCode.TryGetValue(condensed.Replace("FIRST", "1").Replace("SECOND", "2").Replace("THIRD", "3"), out code))
                return code;

            // Special handling: common 4-letter abbrevs that are code + extra letter (e.g., MATT -> MAT)
            if (raw.Length == 4 && _bookNames.ContainsKey(raw.Substring(0,3)))
                return raw.Substring(0,3);

            // Fallback: return the full uppercased token (not truncated) for transparency
            return raw;
        }

        public static string GetName(string code)
        {
            if (string.IsNullOrWhiteSpace(code)) return string.Empty;
            return _bookNames.TryGetValue(code.ToUpper(), out var name) ? name : code.ToUpper();
        }

        public static int GetChapterCount(string code)
        {
            return _chapterCounts.TryGetValue(code.ToUpper(), out var count) ? count : 1; // lean fallback
        }

        public static bool IsValid(string code) => BibleConstants.IsValidBookId(code);
    }
}
