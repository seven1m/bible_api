using Xunit;
using Microsoft.Extensions.Logging;
using BibleImporter.Services;

namespace BibleImporter.Tests;

public class XmlParsingServiceTests
{
    private readonly XmlParsingService _xmlService;

    public XmlParsingServiceTests()
    {
        var logger = new LoggerFactory().CreateLogger<XmlParsingService>();
        _xmlService = new XmlParsingService(logger);
    }

    public void DISABLED_ParseUsfxXml_ValidXml_ReturnsExpectedData()
    {
        // Arrange
        var xmlContent = @"
<usfx>
  <book id=""GEN"">
    <c id=""1""/>
    <v id=""1""/>In the beginning God created the heaven and the earth.
    <v id=""2""/>And the earth was without form, and void; and darkness was upon the face of the deep.
  </book>
</usfx>";

        // Act
        var result = _xmlService.ParseUsfxXml(xmlContent, "test");

        // Assert
        Assert.NotNull(result);
        Assert.Equal("test", result.Translation.Identifier);
        Assert.Single(result.Books);
        
        var book = result.Books.First();
        Assert.Equal("GEN", book.Code);
        Assert.Equal("Genesis", book.Name);
        Assert.Equal(2, book.Verses.Count);
        
        Assert.Equal(1, book.Verses[0].Chapter);
        Assert.Equal(1, book.Verses[0].Verse);
        Assert.Contains("In the beginning", book.Verses[0].Text);
        
        Assert.Equal(1, book.Verses[1].Chapter);
        Assert.Equal(2, book.Verses[1].Verse);
        Assert.Contains("And the earth", book.Verses[1].Text);
    }

    [Fact]
    public void ParseUsfxXml_InvalidXml_ThrowsException()
    {
        // Arrange
        var invalidXml = "<invalid>xml content";

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => 
            _xmlService.ParseUsfxXml(invalidXml, "test"));
    }

    [Fact]
    public void ParseUsfxXml_EmptyContent_ThrowsException()
    {
        // Arrange
        var emptyXml = "";

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => 
            _xmlService.ParseUsfxXml(emptyXml, "test"));
    }
}