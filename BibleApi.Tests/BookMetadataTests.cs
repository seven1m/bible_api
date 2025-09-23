using BibleApi.Core;
using Xunit;

namespace BibleApi.Tests
{
    public class BookMetadataTests
    {
        [Theory]
        [InlineData("Gen", "GEN")] // casing
        [InlineData(" genesis ", "GEN")] // whitespace
        [InlineData("Revelation", "REV")] // full name
        [InlineData("matt", "MAT")] // common abbreviation
        [InlineData("1 Samuel", "1SA")] // number + name with space
        [InlineData("1samuel", "1SA")] // number + name no space
        [InlineData("Song of Solomon", "SNG")] // multi-word
        public void Normalize_ReturnsExpected(string input, string expected)
        {
            var actual = BookMetadata.Normalize(input);
            Assert.Equal(expected, actual);
        }

        [Fact]
        public void Normalize_Unknown_ReturnsTrimmedUpper()
        {
            var input = "FooBar";
            var actual = BookMetadata.Normalize(input);
            Assert.Equal("FOOBAR", actual);
        }

        [Theory]
        [InlineData(null)]
        [InlineData("")]
        [InlineData("   ")]
        public void Normalize_NullOrEmpty_ReturnsEmpty(string? input)
        {
            var actual = BookMetadata.Normalize(input!);
            Assert.Equal(string.Empty, actual);
        }

        [Theory]
        [InlineData(null)]
        [InlineData("")]
        [InlineData("   ")]
        public void GetName_NullOrEmpty_ReturnsEmpty(string? input)
        {
            var actual = BookMetadata.GetName(input!);
            Assert.Equal(string.Empty, actual);
        }

        [Theory]
        [InlineData("GEN", "Genesis")]
        [InlineData("REV", "Revelation")]
        [InlineData("PHP", "Philippians")]
        public void GetName_Known_ReturnsFriendly(string code, string expected)
        {
            Assert.Equal(expected, BookMetadata.GetName(code));
        }

        [Fact]
        public void GetName_Unknown_EchoesCode()
        {
            Assert.Equal("XYZ", BookMetadata.GetName("XYZ"));
        }

        [Theory]
        [InlineData("GEN", 50)]
        [InlineData("PSA", 150)]
        [InlineData("JHN", 21)]
        [InlineData("REV", 22)]
        public void GetChapterCount_Known(string code, int expected)
        {
            Assert.Equal(expected, BookMetadata.GetChapterCount(code));
        }

        [Fact]
        public void GetChapterCount_Unknown_Fallback()
        {
            // Implementation currently falls back to 1 if not found
            Assert.Equal(1, BookMetadata.GetChapterCount("XYZ"));
        }

        [Theory]
        [InlineData("GEN", true)]
        [InlineData("REV", true)]
        [InlineData("XYZ", false)]
        public void IsValid_Works(string code, bool expected)
        {
            Assert.Equal(expected, BookMetadata.IsValid(code));
        }
    }
}
