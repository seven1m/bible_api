using Xunit;
using BibleApi.Core;
using BibleApi.Models;
using BibleApi.Services;

namespace BibleApi.Tests;

public class BibleConstantsTests
{
    [Fact]
    public void ProtestantBooks_Should_Have_66_Books()
    {
        // Arrange & Act
        var bookCount = BibleConstants.ProtestantBooks.Length;
        
        // Assert
        Assert.Equal(66, bookCount);
    }

    [Fact]
    public void OldTestament_Should_Have_39_Books()
    {
        // Arrange & Act
        var bookCount = BibleConstants.OldTestamentBooks.Length;
        
        // Assert
        Assert.Equal(39, bookCount);
    }

    [Fact]
    public void NewTestament_Should_Have_27_Books()
    {
        // Arrange & Act
        var bookCount = BibleConstants.NewTestamentBooks.Length;
        
        // Assert
        Assert.Equal(27, bookCount);
    }

    [Theory]
    [InlineData("GEN", true)]
    [InlineData("REV", true)]
    [InlineData("XYZ", false)]
    [InlineData("", false)]
    public void IsValidBookId_Should_Return_Correct_Result(string bookId, bool expected)
    {
        // Act
        var result = BibleConstants.IsValidBookId(bookId);
        
        // Assert
        Assert.Equal(expected, result);
    }
}

public class MockServiceTests
{
    [Fact]
    public async Task MockService_Should_Return_Translations()
    {
        // Arrange
        var service = new MockAzureXmlBibleService();
        
        // Act
        var translations = await service.ListTranslationsAsync();
        
        // Assert
        Assert.NotEmpty(translations);
        Assert.All(translations, t => Assert.False(string.IsNullOrEmpty(t.Identifier)));
        Assert.All(translations, t => Assert.False(string.IsNullOrEmpty(t.Name)));
    }

    [Fact]
    public async Task MockService_Should_Return_Verses()
    {
        // Arrange
        var service = new MockAzureXmlBibleService();
        
        // Act
        var verses = await service.GetVersesByReferenceAsync("kjv", "GEN", 1);
        
        // Assert
        Assert.NotEmpty(verses);
        Assert.All(verses, v => Assert.False(string.IsNullOrEmpty(v.Text)));
        Assert.All(verses, v => Assert.Equal("GEN", v.BookId));
        Assert.All(verses, v => Assert.Equal(1, v.Chapter));
    }
}