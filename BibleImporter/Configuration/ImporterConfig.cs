using System.ComponentModel.DataAnnotations;

namespace BibleImporter.Configuration
{
    /// <summary>
    /// Configuration settings for the Bible Importer application
    /// </summary>
    public class ImporterConfig
    {
        [Required]
        public string AzureBlobConnectionString { get; set; } = string.Empty;

        [Required]  
        public string BlobContainerName { get; set; } = string.Empty;

        [Required]
        public string SqlConnectionString { get; set; } = string.Empty;
    }
}