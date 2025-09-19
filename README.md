# Bible API (C# .NET Core Edition)

This repository contains a C# .NET Core Web API implementation of a Bible verses and passages API. It serves JSON responses for public domain Bible translations, reading data directly from XML files stored in Azure Blob Storage.

**🎯 This is a complete conversion from the original Python FastAPI implementation to C# .NET Core, maintaining full API compatibility.**

## Projects

- **BibleApi**: Web API service for serving Bible data
- **BibleImporter**: Console application for importing XML Bible data into Azure SQL Database
- **BibleApi.Tests**: Unit tests for the API
- **BibleImporter.Tests**: Unit tests for the importer

## Quick Start

### Using Docker

```bash
# Build the Docker image
docker build -f Dockerfile.dotnet -t bible-api-dotnet:latest .

# Run with environment variables
docker run -p 8000:8000 \
  -e APPSETTINGS__AZURESTORAGECONNECTIONSTRING="your-azure-connection-string" \
  -e APPSETTINGS__AZURECONTAINERNAME="bible-translations" \
  bible-api-dotnet:latest
```

### Running Locally

```bash
# Clone the repository
git clone https://github.com/andreidemit/bible_api.git
cd bible_api/BibleApi

# Install dependencies
dotnet restore

# Set environment variables (optional - will use mock data if not set)
export AppSettings__AzureStorageConnectionString="your-azure-connection-string"
export AppSettings__AzureContainerName="bible-translations"

# Run the application
dotnet run --urls=http://localhost:8000
```

The API will be available at `http://localhost:8000` with automatic Swagger documentation at `/swagger`.

## API Documentation

### Core Endpoints

All endpoints return JSON responses. Full API documentation is available at `/swagger` when running the application.

#### List Translations
```
GET /v1/data
```
Returns a list of all available Bible translations.

#### Get Books for Translation
```
GET /v1/data/{translationId}
```
Returns all books available in the specified translation.

#### Get Chapters for Book
```
GET /v1/data/{translationId}/{bookId}
```
Returns all chapters for the specified book in the translation.

#### Get Verses for Chapter
```
GET /v1/data/{translationId}/{bookId}/{chapter}
```
Returns all verses for the specified chapter.

#### Random Verse
```
GET /v1/data/{translationId}/random/{bookId}
```
Returns a random verse from the specified book(s). Use `OT` for Old Testament, `NT` for New Testament, or specific book IDs separated by commas.

#### Health Check
```
GET /healthz
```
Returns API health status.

### Example API Calls

```bash
# List all translations
curl http://localhost:8000/v1/data

# Get books in King James Version
curl http://localhost:8000/v1/data/kjv

# Get chapters in Genesis
curl http://localhost:8000/v1/data/kjv/GEN

# Get verses from John chapter 3
curl http://localhost:8000/v1/data/kjv/JHN/3

# Get random verse from New Testament
curl http://localhost:8000/v1/data/kjv/random/NT
```

## Configuration

The application uses the .NET configuration system. Settings can be provided via:

- `appsettings.json` file
- Environment variables (prefixed with `AppSettings__`)
- Command line arguments
- Azure Key Vault (in production)

### Required Settings

| Setting | Environment Variable | Description |
|---------|---------------------|-------------|
| `AzureStorageConnectionString` | `AppSettings__AzureStorageConnectionString` | Azure Storage connection string for Bible XML files |
| `AzureContainerName` | `AppSettings__AzureContainerName` | Container name (default: "bible-translations") |

### Optional Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `Environment` | "development" | Application environment |
| `AllowedOrigins` | ["*"] | CORS allowed origins |
| `AllowedMethods` | ["GET", "OPTIONS"] | CORS allowed methods |
| `AllowedHeaders` | ["Content-Type"] | CORS allowed headers |

## Development

### Project Structure

```
BibleApi/
├── Controllers/         # API controllers
│   └── BibleController.cs
├── Models/             # Data models and DTOs
│   └── BibleModels.cs
├── Services/           # Business logic services
│   ├── IAzureXmlBibleService.cs
│   ├── AzureXmlBibleService.cs
│   └── MockAzureXmlBibleService.cs
├── Configuration/      # Configuration classes
│   └── AppSettings.cs
├── Core/              # Core utilities and constants
│   └── BibleConstants.cs
└── Program.cs         # Application entry point
```

### Building and Testing

```bash
# Build the project
dotnet build

# Run tests (when implemented)
dotnet test

# Run with hot reload for development
dotnet watch run --urls=http://localhost:8000
```

### Mock Mode

For development and testing without Azure Storage, the application automatically uses a mock service when no Azure connection string is configured. The mock service provides sample data for all endpoints.

## Features

- ✅ RESTful API with versioned endpoints (`/v1/`)
- ✅ CORS support for cross-origin requests
- ✅ Automatic OpenAPI/Swagger documentation
- ✅ Health check endpoint for monitoring
- ✅ Azure Blob Storage integration
- ✅ In-memory caching for performance
- ✅ Structured logging with .NET ILogger
- ✅ Docker containerization
- ✅ Configuration management with .NET Options pattern
- ✅ Dependency injection
- ✅ Error handling with proper HTTP status codes

## Deployment

### Docker

The application includes a multi-stage Dockerfile optimized for production:

```dockerfile
# Build stage uses .NET SDK
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
# ... build steps ...

# Runtime stage uses minimal ASP.NET runtime
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
# ... runtime configuration ...
```

### Azure Container Instances

```bash
# Deploy to Azure Container Instances
az container create \
  --resource-group myResourceGroup \
  --name bible-api \
  --image bible-api-dotnet:latest \
  --environment-variables AppSettings__AzureStorageConnectionString="$CONNECTION_STRING" \
  --ports 8000
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bible-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bible-api
  template:
    metadata:
      labels:
        app: bible-api
    spec:
      containers:
      - name: bible-api
        image: bible-api-dotnet:latest
        ports:
        - containerPort: 8000
        env:
        - name: AppSettings__AzureStorageConnectionString
          valueFrom:
            secretKeyRef:
              name: bible-api-secrets
              key: azure-storage-connection-string
```

## Technology Stack

- **Framework**: ASP.NET Core 8.0
- **Language**: C# 12
- **Cloud Storage**: Azure Blob Storage
- **Documentation**: Swagger/OpenAPI
- **Containerization**: Docker
- **XML Processing**: System.Xml.Linq
- **Dependency Injection**: Built-in .NET DI container
- **Configuration**: .NET Configuration API
- **Logging**: .NET ILogger

## Migration from Python

This C# implementation maintains 100% API compatibility with the original Python FastAPI version. All endpoints, response formats, and behaviors are preserved. Key improvements include:

- **Better Performance**: Compiled C# with optimized runtime
- **Type Safety**: Strong typing throughout the application
- **Better Tooling**: Rich IDE support and debugging
- **Enterprise Ready**: Built on proven .NET platform
- **Memory Efficiency**: Better memory management than Python
- **Async/Await**: Native async support throughout

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

- **Source Code**: MIT License (see `LICENSE`)
- **Bible Translations**: All Bible translations are public domain
- **Original Python Implementation**: © 2014 Tim Morgan (retained per MIT requirements)
- **C# Port**: © 2025 Andrei Demit

## Support

- 📖 **Documentation**: Available at `/swagger` endpoint
- 🐛 **Issues**: [GitHub Issues](https://github.com/andreidemit/bible_api/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/andreidemit/bible_api/discussions)

---

**Note**: This is a complete rewrite in C# .NET Core while maintaining full backward compatibility with the original Python FastAPI version. Both implementations can be used interchangeably.

# Deprecated

Content merged into root README.md. Use `README.md` for all documentation.