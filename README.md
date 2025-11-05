# Bible API (.NET 9)

A modern, high-performance Bible verses and passages API built with C# .NET 9. Serves JSON responses for public domain Bible translations, reading data directly from XML files stored in Azure Blob Storage.

**🚀 Recently Modernized:** Fully migrated to .NET 9 with Infrastructure as Code (Terraform) and production-ready Docker setup.

## ✨ Features

- 🎯 **RESTful API** with versioned endpoints (`/v1/*`)
- 📖 **Multiple Bible translations** support
- 🔍 **Search functionality** across verses
- 🎲 **Random verse** generator
- 📊 **Swagger/OpenAPI** documentation
- ⚡ **In-memory caching** for performance
- 🐳 **Docker** containerization
- ☁️ **Azure** cloud-ready
- 🏗️ **Infrastructure as Code** (Terraform)
- 🧪 **Unit tests** with xUnit

## 📁 Project Structure

```
bible_api/
├── src/
│   └── BibleApi/              # Main API project (.NET 9)
│       ├── Controllers/       # API endpoints
│       ├── Services/          # Business logic
│       ├── Models/            # DTOs and domain models
│       ├── Core/              # Shared utilities
│       └── Configuration/     # App settings
├── tests/
│   └── BibleApi.Tests/        # Unit tests (xUnit)
├── docker/
│   ├── Dockerfile             # .NET 9 Alpine image
│   ├── docker-compose.yml     # Full local dev environment
│   └── README.md              # Docker documentation
├── infrastructure/
│   ├── terraform/             # Azure IaC
│   │   ├── main.tf           # Main resources
│   │   ├── variables.tf      # Configuration
│   │   └── modules/          # Reusable modules
│   └── sql/                   # Database scripts
└── docs/                      # Documentation
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/andreidemit/bible_api.git
cd bible_api

# Start all services (API + Redis + SQL + Adminer)
cd docker
docker-compose up
```

**Services Available:**
- 🌐 **API**: http://localhost:8000
- 📚 **Swagger UI**: http://localhost:8000/swagger
- 🗄️ **Database Admin**: http://localhost:8081
- 🔴 **Redis Commander**: http://localhost:8082

### Option 2: Docker Only

```bash
# Build the image
docker build -f docker/Dockerfile -t bible-api:latest .

# Run container
docker run -p 8000:8000 \
  -e ASPNETCORE_ENVIRONMENT=Development \
  -e AppSettings__AzureStorageConnectionString="your-connection-string" \
  bible-api:latest
```

### Option 3: Local Development (.NET 9 SDK Required)

```bash
# Install .NET 9 SDK
# https://dotnet.microsoft.com/download/dotnet/9.0

# Restore dependencies
dotnet restore

# Run the API
cd src/BibleApi
dotnet run
```

## 📖 API Documentation

### Core Endpoints

All endpoints return JSON. Full interactive docs at `/swagger`.

#### 1. List All Translations
```http
GET /v1/data
```

**Response:**
```json
{
  "translations": [
    {
      "identifier": "kjv",
      "name": "King James Version",
      "language": "english",
      "languageCode": "en",
      "license": "Public Domain",
      "url": "http://localhost:8000/v1/data/kjv"
    }
  ]
}
```

#### 2. Get Books in Translation
```http
GET /v1/data/{translationId}
```

**Example:** `/v1/data/kjv`

#### 3. Get Chapters in Book
```http
GET /v1/data/{translationId}/{bookId}
```

**Example:** `/v1/data/kjv/GEN`

#### 4. Get Verses in Chapter
```http
GET /v1/data/{translationId}/{bookId}/{chapter}?verse_start=1&verse_end=10
```

**Example:** `/v1/data/kjv/JHN/3?verse_start=16&verse_end=17`

#### 5. Random Verse
```http
GET /v1/data/{translationId}/random/{bookIds}
```

**Examples:**
- `/v1/data/kjv/random/OT` - Random from Old Testament
- `/v1/data/kjv/random/NT` - Random from New Testament
- `/v1/data/kjv/random/GEN,EXO` - Random from Genesis or Exodus

#### 6. Search Verses
```http
GET /v1/search/{translationId}?q={searchTerm}&limit=25
```

**Example:** `/v1/search/kjv?q=faith&limit=10`

#### 7. Health Check
```http
GET /healthz
```

### Example Usage

```bash
# List translations
curl http://localhost:8000/v1/data

# Get John 3:16
curl http://localhost:8000/v1/data/kjv/JHN/3?verse_start=16&verse_end=16

# Search for "love"
curl http://localhost:8000/v1/search/kjv?q=love&limit=5

# Random verse from Psalms
curl http://localhost:8000/v1/data/kjv/random/PSA
```

## 🏗️ Infrastructure as Code

Deploy to Azure using Terraform:

```bash
cd infrastructure/terraform

# Copy example config
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy
terraform apply
```

**Resources Created:**
- Resource Group
- Azure Blob Storage (for Bible XML files)
- Container Registry (for Docker images)
- App Service Plan + App Service (Linux)
- Application Insights (monitoring)
- SQL Database (optional)

See `infrastructure/terraform/README.md` for details.

## 🐳 Docker Deployment

### Build for Production

```bash
# Build optimized image
docker build -f docker/Dockerfile -t bible-api:latest .

# Tag for Azure Container Registry
docker tag bible-api:latest myregistry.azurecr.io/bible-api:v1.0.0

# Push to ACR
docker push myregistry.azurecr.io/bible-api:v1.0.0
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ASPNETCORE_ENVIRONMENT` | Environment name | `Production` |
| `AppSettings__AzureStorageConnectionString` | Azure Blob connection | Required |
| `AppSettings__AzureContainerName` | Blob container name | `bible-translations` |
| `ConnectionStrings__Redis` | Redis connection (optional) | - |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | App Insights (optional) | - |

## 🧪 Testing

```bash
# Run all tests
dotnet test

# Run with coverage
dotnet test /p:CollectCoverage=true

# Run specific test
dotnet test --filter "FullyQualifiedName~BookMetadataTests"
```

## 📊 Technology Stack

- **Framework**: .NET 9.0
- **Language**: C# 13
- **Web Framework**: ASP.NET Core
- **Cloud Storage**: Azure Blob Storage
- **Database**: Azure SQL (optional)
- **Caching**: Redis (optional, in-memory by default)
- **Documentation**: Swagger/OpenAPI
- **Testing**: xUnit
- **Container**: Docker (Alpine-based)
- **IaC**: Terraform
- **CI/CD**: GitHub Actions (planned)

## 🔧 Configuration

### appsettings.json

```json
{
  "AppSettings": {
    "AzureStorageConnectionString": "DefaultEndpointsProtocol=https;AccountName=...",
    "AzureContainerName": "bible-translations"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  }
}
```

### Development Mode

When `AzureStorageConnectionString` is not configured in Development environment, the API uses mock data with sample verses.

## 📚 Bible Data Format

The API expects Bible translations in XML format (USFX/OSIS) stored in Azure Blob Storage:

```
bible-translations/
├── kjv.xml
├── asv.xml
├── web.xml
└── ...
```

## 🔒 Security

- ✅ HTTPS enforced in production
- ✅ Non-root user in Docker
- ✅ CORS configured
- ✅ Health checks enabled
- ✅ Secrets via environment variables
- ✅ Input validation on all endpoints

## 📈 Performance

- **In-memory caching** with configurable TTL
- **Response compression** (Gzip)
- **Async/await** throughout
- **Minimal allocations** with modern C#
- **Alpine-based images** for small container size (~180MB)

## 🚀 Roadmap

- [ ] Full-text search with Azure Cognitive Search
- [ ] Redis distributed caching
- [ ] Rate limiting middleware
- [ ] GraphQL API
- [ ] WebSocket support for real-time updates
- [ ] Mobile SDK (Xamarin/MAUI)
- [ ] Verse comparison across translations
- [ ] Audio verse playback

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file.

Bible texts are sourced from public domain translations. See [DATA_LICENSES.md](docs/DATA_LICENSES.md) for attribution.

## 💬 Support

- 📧 **Issues**: [GitHub Issues](https://github.com/andreidemit/bible_api/issues)
- 📖 **Documentation**: See `/docs` folder
- 🐛 **Bug Reports**: Use issue templates

## 🙏 Acknowledgments

- Original Python implementation contributors
- Public domain Bible translation providers
- .NET and Azure communities

---

**Built with ❤️ using .NET 9**
