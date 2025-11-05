using System.ComponentModel.DataAnnotations;

namespace BibleApi.Configuration
{
    /// <summary>
    /// Application settings (equivalent to Python Settings class)
    /// </summary>
    public class AppSettings
    {
        /// <summary>
        /// Azure Storage connection string for Bible XML files
        /// </summary>
        [Required]
        public string AzureStorageConnectionString { get; set; } = string.Empty;

        /// <summary>
        /// Azure container name containing Bible translations
        /// </summary>
        public string AzureContainerName { get; set; } = "bible-translations";

        /// <summary>
        /// Application environment (development, production, etc.)
        /// </summary>
        public string Environment { get; set; } = "development";

        /// <summary>
        /// Base URL for the API (used for generating URLs in responses)
        /// </summary>
        public string BaseUrl { get; set; } = string.Empty;

        /// <summary>
        /// CORS allowed origins
        /// </summary>
        public string[] AllowedOrigins { get; set; } = new[] { "*" };

        /// <summary>
        /// CORS allowed methods
        /// </summary>
        public string[] AllowedMethods { get; set; } = new[] { "GET", "OPTIONS" };

        /// <summary>
        /// CORS allowed headers
        /// </summary>
        public string[] AllowedHeaders { get; set; } = new[] { "Content-Type" };
    }
}