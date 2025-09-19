using Azure.Storage.Blobs;
using BibleImporter.Configuration;
using Microsoft.Extensions.Logging;

namespace BibleImporter.Services
{
    /// <summary>
    /// Service for retrieving XML files from Azure Blob Storage
    /// </summary>
    public class BlobStorageService
    {
        private readonly BlobServiceClient _blobServiceClient;
        private readonly BlobContainerClient _containerClient;
        private readonly ILogger<BlobStorageService> _logger;

        public BlobStorageService(ImporterConfig config, ILogger<BlobStorageService> logger)
        {
            _logger = logger;
            
            try
            {
                _blobServiceClient = new BlobServiceClient(config.AzureBlobConnectionString);
                _containerClient = _blobServiceClient.GetBlobContainerClient(config.BlobContainerName);
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Failed to initialize Azure Blob Storage client: {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Search for XML file by book name and retrieve content
        /// </summary>
        public async Task<string?> GetXmlFileByBookNameAsync(string bookName)
        {
            try
            {
                // Normalize the book name for searching
                var normalizedBookName = bookName.Trim().ToLowerInvariant();
                
                // Search for files that might match the book name
                var matchingBlobs = new List<string>();

                await foreach (var blobItem in _containerClient.GetBlobsAsync())
                {
                    var fileName = blobItem.Name.ToLowerInvariant();
                    
                    // Check if filename contains the book name or matches common patterns
                    if (fileName.Contains(normalizedBookName) || 
                        fileName.Contains(normalizedBookName.Replace(" ", "")) ||
                        fileName.Contains(normalizedBookName.Replace(" ", "_")) ||
                        fileName.Contains(normalizedBookName.Replace(" ", "-")))
                    {
                        matchingBlobs.Add(blobItem.Name);
                    }
                }

                // If no matches found, try looking for exact filename patterns
                if (!matchingBlobs.Any())
                {
                    var potentialNames = new[]
                    {
                        $"{normalizedBookName}.xml",
                        $"{normalizedBookName.Replace(" ", "")}.xml",
                        $"{normalizedBookName.Replace(" ", "_")}.xml",
                        $"{normalizedBookName.Replace(" ", "-")}.xml"
                    };

                    foreach (var potentialName in potentialNames)
                    {
                        try
                        {
                            var blobClient = _containerClient.GetBlobClient(potentialName);
                            if (await blobClient.ExistsAsync())
                            {
                                matchingBlobs.Add(potentialName);
                                break;
                            }
                        }
                        catch
                        {
                            // Continue trying other names
                        }
                    }
                }

                if (!matchingBlobs.Any())
                {
                    _logger.LogWarning("No XML file found for book name: {BookName}", bookName);
                    return null;
                }

                // Use the first match (could be enhanced to pick the best match)
                var selectedBlob = matchingBlobs.First();
                _logger.LogInformation("Found matching XML file: {FileName} for book: {BookName}", selectedBlob, bookName);

                return await GetXmlContentAsync(selectedBlob);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error searching for XML file for book: {BookName}", bookName);
                throw;
            }
        }

        /// <summary>
        /// Get XML content from specific blob
        /// </summary>
        public async Task<string?> GetXmlContentAsync(string blobName)
        {
            try
            {
                var blobClient = _containerClient.GetBlobClient(blobName);
                
                if (!await blobClient.ExistsAsync())
                {
                    _logger.LogWarning("Blob not found: {BlobName}", blobName);
                    return null;
                }

                var response = await blobClient.DownloadContentAsync();
                return response.Value.Content.ToString();
            }
            catch (Azure.RequestFailedException ex) when (ex.Status == 404)
            {
                _logger.LogWarning("Blob not found: {BlobName}", blobName);
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error downloading blob: {BlobName}", blobName);
                throw;
            }
        }

        /// <summary>
        /// List all available XML files in the container
        /// </summary>
        public async Task<List<string>> ListXmlFilesAsync()
        {
            var xmlFiles = new List<string>();

            try
            {
                await foreach (var blobItem in _containerClient.GetBlobsAsync())
                {
                    if (blobItem.Name.EndsWith(".xml", StringComparison.OrdinalIgnoreCase))
                    {
                        xmlFiles.Add(blobItem.Name);
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error listing XML files");
                throw;
            }

            return xmlFiles;
        }

        /// <summary>
        /// Test blob storage connection
        /// </summary>
        public async Task<bool> TestConnectionAsync()
        {
            try
            {
                await _containerClient.GetPropertiesAsync();
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Blob storage connection test failed");
                return false;
            }
        }
    }
}