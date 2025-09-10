# Azure Blob Storage Configuration for Bible API

The Bible API now supports reading XML source files from Azure Blob Storage, allowing you to store your Bible translation files in the cloud instead of local storage.

## Prerequisites

1. An Azure Storage Account
2. A blob container to store your Bible XML files
3. The `azure-storage-blob` Python package (already included in requirements.txt)

## Configuration

Set one of the following environment variable combinations:

### Option 1: Connection String (Recommended)
```bash
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=mykey;EndpointSuffix=core.windows.net"
AZURE_STORAGE_CONTAINER_NAME="bibles"  # Optional, defaults to "bibles"
```

### Option 2: Account Name and Key
```bash
AZURE_STORAGE_ACCOUNT_NAME="mystorageaccount"
AZURE_STORAGE_ACCOUNT_KEY="myaccountkey"
AZURE_STORAGE_CONTAINER_NAME="bibles"  # Optional, defaults to "bibles"
```

## Setup Steps

### 1. Create Azure Storage Resources

#### Using Azure Portal:
1. Create a Storage Account in the Azure Portal
2. Create a blob container (e.g., "bibles")
3. Upload your Bible XML files to the container
4. Get your connection string from the Storage Account keys

#### Using Azure CLI:
```bash
# Create resource group
az group create --name bible-api-rg --location eastus

# Create storage account
az storage account create \
  --name yourstorageaccount \
  --resource-group bible-api-rg \
  --location eastus \
  --sku Standard_LRS

# Create container
az storage container create \
  --name bibles \
  --account-name yourstorageaccount

# Get connection string
az storage account show-connection-string \
  --name yourstorageaccount \
  --resource-group bible-api-rg
```

### 2. Upload Bible XML Files

#### Using Azure Portal:
1. Navigate to your storage account
2. Go to the "bibles" container
3. Upload your XML files

#### Using Azure CLI:
```bash
# Upload files
az storage blob upload \
  --file path/to/eng-kjv.osis.xml \
  --name eng-kjv.osis.xml \
  --container-name bibles \
  --connection-string "$AZURE_STORAGE_CONNECTION_STRING"
```

#### Using Python Script:
```python
from azure.storage.blob import BlobServiceClient
import os

# Initialize client
connection_string = "your_connection_string_here"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_name = "bibles"

# Upload a file
def upload_bible_file(local_file_path, blob_name):
    blob_client = blob_service_client.get_blob_client(
        container=container_name, 
        blob=blob_name
    )
    with open(local_file_path, 'rb') as data:
        blob_client.upload_blob(data, overwrite=True)
    print(f"Uploaded {blob_name}")

# Example usage
upload_bible_file("bibles/eng-kjv.osis.xml", "eng-kjv.osis.xml")
```

### 3. Configure Your Application

Set the environment variables in your `.env` file:
```bash
# Database configuration (required)
DATABASE_URL=mysql+pymysql://user:password@host:port/database

# Azure Blob Storage configuration
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=youraccount;AccountKey=yourkey;EndpointSuffix=core.windows.net"
AZURE_STORAGE_CONTAINER_NAME="bibles"
```

### 4. Import Bible Translations

The import process works the same as before, but now reads from Azure Blob Storage:

```bash
# Import all translations from Azure Blob Storage
python import_bible.py

# Import specific translation
python import_bible.py -t eng-kjv.osis.xml

# Drop and recreate tables first
python import_bible.py --drop-tables
```

## Testing Your Configuration

Use the provided test script to verify your Azure Blob Storage configuration:

```bash
python test_azure_storage.py
```

This will test:
- Azure SDK availability
- Configuration validity
- Blob storage connectivity
- File listing capabilities

## Supported File Formats

The importer supports OSIS XML files with the following namespace:
```xml
xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace"
```

Both modern OSIS format (with sID/eID verse markers) and legacy formats are supported.

## Fallback Behavior

If Azure Blob Storage is not configured or unavailable, the system automatically falls back to reading local files from the `bibles/` directory. This ensures:
- Development environments work without Azure setup
- Graceful degradation when Azure services are unavailable
- Easy migration from local to cloud storage

## Security Best Practices

1. **Use Connection Strings**: Prefer connection strings over account name/key pairs
2. **Environment Variables**: Store credentials in environment variables, never in code
3. **Container Permissions**: Use private blob containers and access them via connection string
4. **Key Rotation**: Regularly rotate your storage account keys
5. **Network Security**: Consider using Azure Private Endpoints for production deployments

## Troubleshooting

### Common Issues:

1. **"Azure Blob Storage not configured"**
   - Verify environment variables are set correctly
   - Check that `azure-storage-blob` package is installed

2. **"Failed to read from Azure Blob Storage"**
   - Verify your connection string is correct
   - Check that the container name matches
   - Ensure the blob files exist in the container

3. **"No XML files found"**
   - Verify files were uploaded to the correct container
   - Check file names match the README.md translation table

4. **Authentication errors**
   - Verify your storage account key or connection string
   - Check that the storage account exists and is accessible

### Debug Mode:
The importer provides verbose logging. You'll see messages like:
```
Azure Blob Storage configured with connection string (container: bibles)
Found 24 XML files in Azure Blob Storage container 'bibles'
read from Azure Blob Storage: eng-kjv.osis.xml
```

## Migration Guide

### From Local Files to Azure Blob Storage:

1. **Upload existing files**: Use the Azure Portal, CLI, or Python script to upload your existing XML files
2. **Set environment variables**: Configure your Azure connection
3. **Test the configuration**: Run `python test_azure_storage.py`
4. **Run import**: Execute `python import_bible.py` as usual

The system will automatically detect and use Azure Blob Storage when configured.

## Cost Considerations

- **Storage costs**: Standard blob storage is very cost-effective
- **Transaction costs**: Minimal for typical import operations
- **Bandwidth**: Consider data transfer costs if importing frequently from different regions

For most Bible API deployments, Azure Blob Storage costs will be minimal (typically less than $1/month for storage of all Bible translations).