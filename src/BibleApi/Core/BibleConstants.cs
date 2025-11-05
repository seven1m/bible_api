namespace BibleApi.Core
{
    /// <summary>
    /// Canonical book lists and derived subsets (equivalent to Python constants.py)
    /// </summary>
    public static class BibleConstants
    {
        /// <summary>
        /// Complete list of Protestant Bible books in canonical order
        /// </summary>
        public static readonly string[] ProtestantBooks = new[]
        {
            "GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT", "1SA", "2SA", "1KI", "2KI",
            "1CH", "2CH", "EZR", "NEH", "EST", "JOB", "PSA", "PRO", "ECC", "SNG", "ISA", "JER",
            "LAM", "EZK", "DAN", "HOS", "JOL", "AMO", "OBA", "JON", "MIC", "NAM", "HAB", "ZEP",
            "HAG", "ZEC", "MAL", "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL",
            "EPH", "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS", "1PE",
            "2PE", "1JN", "2JN", "3JN", "JUD", "REV"
        };

        /// <summary>
        /// Old Testament books (from Genesis to Malachi)
        /// </summary>
        public static readonly string[] OldTestamentBooks = ProtestantBooks.Take(39).ToArray();

        /// <summary>
        /// New Testament books (from Matthew to Revelation)
        /// </summary>
        public static readonly string[] NewTestamentBooks = ProtestantBooks.Skip(39).ToArray();

        /// <summary>
        /// Check if a book ID is valid
        /// </summary>
        /// <param name="bookId">Book identifier to validate</param>
        /// <returns>True if the book ID is valid</returns>
        public static bool IsValidBookId(string bookId)
        {
            return ProtestantBooks.Contains(bookId?.ToUpper());
        }

        /// <summary>
        /// Get the canonical order of a book (0-based index)
        /// </summary>
        /// <param name="bookId">Book identifier</param>
        /// <returns>Index of the book in canonical order, or -1 if not found</returns>
        public static int GetBookOrder(string bookId)
        {
            return Array.IndexOf(ProtestantBooks, bookId?.ToUpper());
        }

        /// <summary>
        /// Check if a book is in the Old Testament
        /// </summary>
        /// <param name="bookId">Book identifier</param>
        /// <returns>True if the book is in the Old Testament</returns>
        public static bool IsOldTestament(string bookId)
        {
            return OldTestamentBooks.Contains(bookId?.ToUpper());
        }

        /// <summary>
        /// Check if a book is in the New Testament
        /// </summary>
        /// <param name="bookId">Book identifier</param>
        /// <returns>True if the book is in the New Testament</returns>
        public static bool IsNewTestament(string bookId)
        {
            return NewTestamentBooks.Contains(bookId?.ToUpper());
        }
    }
}