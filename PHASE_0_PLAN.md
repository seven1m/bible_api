# PHASE 0: Foundation Restructuring
## Clean Up, Modernize, and Infrastructure as Code

**Status**: Ready for Implementation
**Priority**: FOUNDATIONAL (must complete before other phases)
**Estimated Time**: 2-3 days

---

## 🎯 OBJECTIVES

1. ✅ Remove BibleImporter project and all related code
2. ✅ Clean up unnecessary files and dependencies
3. ✅ Upgrade to .NET 9 with modern best practices
4. ✅ Create Infrastructure as Code (Terraform for Azure)
5. ✅ Modernize Dockerfile with .NET 9
6. ✅ Create comprehensive docker-compose.yml for local development
7. ✅ Restructure project following .NET 9 conventions

---

## 📋 CURRENT STATE ANALYSIS

### Projects in Solution:
- ✅ **BibleApi** (Keep) - Main API project
- ✅ **BibleApi.Tests** (Keep) - Unit tests
- ❌ **BibleImporter** (Remove) - Data import tool, not needed for API

### Files/Folders:
- ✅ **BibleApi/** - Main API code
- ✅ **BibleApi.Tests/** - Tests
- ❌ **BibleImporter/** - To be removed
- ⚠️ **sql/** - Database scripts (keep for IaC reference, move to infrastructure)
- ⚠️ **static/** - favicon.svg (keep, move to wwwroot)
- ❌ **docker-compose.yml** - Empty/deprecated (recreate)
- ✅ **Dockerfile** - Exists but targets .NET 8 (update to .NET 9)

### Issues Found:
1. Solution references phantom project (GUID {B51E31AF...})
2. Dockerfile references BibleImporter
3. docker-compose.yml is deprecated/empty
4. Using .NET 8 instead of .NET 9
5. No Infrastructure as Code
6. Static files not in standard wwwroot location

---

## 🗑️ TASK 1: REMOVE BIBLEIMPORTER (30 minutes)

### Actions:
1. Delete BibleImporter folder entirely
2. Remove from solution file (BibleApi.sln)
3. Update Dockerfile to remove BibleImporter references
4. Remove any dependencies in other projects
5. Update .gitignore if needed
6. Clean up any import-related documentation

### Files to Delete:
```
BibleImporter/
  ├── BibleImporter.csproj
  ├── Configuration/
  ├── Models/
  ├── Services/
  │   ├── BlobStorageService.cs
  │   ├── DatabaseService.cs
  │   └── XmlParsingService.cs
  ├── BibleImporterApp.cs
  └── Program.cs
```

### Files to Update:
- `BibleApi.sln` - Remove BibleImporter project reference
- `Dockerfile` - Remove BibleImporter copy/restore lines

---

## 🧹 TASK 2: CLEAN UP PROJECT STRUCTURE (30 minutes)

### Reorganize Files:
```
Before:
bible_api/
├── static/favicon.svg
├── sql/*.sql
├── BibleApi/
└── BibleApi.Tests/

After:
bible_api/
├── src/
│   └── BibleApi/
│       ├── wwwroot/
│       │   └── favicon.svg
│       ├── Controllers/
│       ├── Services/
│       ├── Models/
│       ├── Core/
│       └── Configuration/
├── tests/
│   └── BibleApi.Tests/
├── infrastructure/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   └── sql/
│       ├── db_creation_script.sql
│       └── migrations/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
└── docs/
    └── (existing .md files)
```

### Actions:
1. Create `src/` folder and move BibleApi
2. Create `tests/` folder and move BibleApi.Tests
3. Create `infrastructure/` folder for IaC
4. Create `docker/` folder for container files
5. Move `static/favicon.svg` to `src/BibleApi/wwwroot/`
6. Move `sql/` to `infrastructure/sql/`
7. Move docs to `docs/` folder
8. Update all paths in solution and project files

---

## 🚀 TASK 3: UPGRADE TO .NET 9 (1 hour)

### .NET 9 Best Practices to Implement:

#### 1. **Use Minimal APIs (if applicable)**
Current: Controller-based API
Option: Keep controllers (good for complex APIs) or migrate to minimal APIs

**Recommendation**: Keep controllers but modernize them

#### 2. **Enable Native AOT (optional)**
For faster startup and lower memory

#### 3. **Use Primary Constructors**
```csharp
// Old (.NET 8)
public class BibleController : ControllerBase
{
    private readonly IAzureXmlBibleService _service;
    public BibleController(IAzureXmlBibleService service) => _service = service;
}

// New (.NET 9)
public class BibleController(IAzureXmlBibleService service) : ControllerBase
{
    // _service available directly
}
```

#### 4. **Use Collection Expressions**
```csharp
// Old
var books = new List<string> { "GEN", "EXO" };

// New
var books = ["GEN", "EXO"];
```

#### 5. **Modern Configuration**
```csharp
// Use new WebApplication.CreateBuilder() optimizations
var builder = WebApplication.CreateSlimBuilder(args);
```

#### 6. **Improved Logging with LoggerMessage**
```csharp
// Source-generated logging for performance
public partial class BibleService
{
    [LoggerMessage(Level = LogLevel.Information, Message = "Loading translation {TranslationId}")]
    partial void LogLoadingTranslation(string translationId);
}
```

### Update Files:
- `BibleApi/BibleApi.csproj` - Change TargetFramework to `net9.0`
- `BibleApi.Tests/BibleApi.Tests.csproj` - Change to `net9.0`
- Update all package references to .NET 9 compatible versions
- Update Program.cs with .NET 9 patterns

---

## 🏗️ TASK 4: INFRASTRUCTURE AS CODE - TERRAFORM (2-3 hours)

### Create Terraform Structure:

```
infrastructure/terraform/
├── main.tf              # Main infrastructure definition
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── terraform.tfvars     # Default values (gitignored)
├── terraform.tfvars.example  # Template
├── modules/
│   ├── app-service/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── blob-storage/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── sql-database/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── README.md
```

### Resources to Create:

#### 1. **Resource Group**
```hcl
resource "azurerm_resource_group" "bible_api" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}
```

#### 2. **Azure Blob Storage**
```hcl
resource "azurerm_storage_account" "bible_storage" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.bible_api.name
  location                 = azurerm_resource_group.bible_api.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  blob_properties {
    cors_rule {
      allowed_origins    = ["*"]
      allowed_methods    = ["GET"]
      allowed_headers    = ["*"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 3600
    }
  }
}

resource "azurerm_storage_container" "bible_translations" {
  name                  = "bible-translations"
  storage_account_name  = azurerm_storage_account.bible_storage.name
  container_access_type = "private"
}
```

#### 3. **Azure SQL Database (Optional)**
```hcl
resource "azurerm_mssql_server" "bible_sql" {
  name                         = var.sql_server_name
  resource_group_name          = azurerm_resource_group.bible_api.name
  location                     = azurerm_resource_group.bible_api.location
  version                      = "12.0"
  administrator_login          = var.sql_admin_username
  administrator_login_password = var.sql_admin_password
}

resource "azurerm_mssql_database" "bible_db" {
  name      = var.sql_database_name
  server_id = azurerm_mssql_server.bible_sql.id
  sku_name  = "Basic"
}
```

#### 4. **Azure App Service**
```hcl
resource "azurerm_service_plan" "bible_api" {
  name                = var.app_service_plan_name
  resource_group_name = azurerm_resource_group.bible_api.name
  location            = azurerm_resource_group.bible_api.location
  os_type             = "Linux"
  sku_name            = "B1"
}

resource "azurerm_linux_web_app" "bible_api" {
  name                = var.app_service_name
  resource_group_name = azurerm_resource_group.bible_api.name
  location            = azurerm_resource_group.bible_api.location
  service_plan_id     = azurerm_service_plan.bible_api.id

  site_config {
    application_stack {
      docker_image_name = "bible-api:latest"
    }

    health_check_path = "/healthz"
  }

  app_settings = {
    "AppSettings__AzureStorageConnectionString" = azurerm_storage_account.bible_storage.primary_connection_string
    "AppSettings__AzureContainerName"          = "bible-translations"
  }
}
```

#### 5. **Azure Container Registry**
```hcl
resource "azurerm_container_registry" "bible_acr" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.bible_api.name
  location            = azurerm_resource_group.bible_api.location
  sku                 = "Basic"
  admin_enabled       = true
}
```

#### 6. **Application Insights** (Optional)
```hcl
resource "azurerm_application_insights" "bible_api" {
  name                = var.app_insights_name
  resource_group_name = azurerm_resource_group.bible_api.name
  location            = azurerm_resource_group.bible_api.location
  application_type    = "web"
}
```

### Variables (variables.tf):
```hcl
variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-bible-api"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# ... more variables
```

---

## 🐳 TASK 5: MODERNIZE DOCKER SETUP (1 hour)

### New Dockerfile (docker/Dockerfile):
```dockerfile
#############################
# Bible API - .NET 9 Production Image
#############################

# Build stage
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
ARG BUILD_CONFIGURATION=Release
WORKDIR /src

# Copy solution and project files
COPY BibleApi.sln ./
COPY src/BibleApi/BibleApi.csproj src/BibleApi/
COPY tests/BibleApi.Tests/BibleApi.Tests.csproj tests/BibleApi.Tests/

# Restore dependencies
RUN dotnet restore BibleApi.sln

# Copy source and build
COPY src/BibleApi/ src/BibleApi/
COPY tests/BibleApi.Tests/ tests/BibleApi.Tests/

WORKDIR /src/src/BibleApi
RUN dotnet build -c $BUILD_CONFIGURATION -o /app/build --no-restore

# Publish
RUN dotnet publish -c $BUILD_CONFIGURATION -o /app/publish \
    /p:UseAppHost=false --no-restore

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:9.0-alpine AS runtime

# Install curl for health checks
RUN apk add --no-cache curl

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

WORKDIR /app

# Copy published app
COPY --from=build --chown=appuser:appgroup /app/publish .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz || exit 1

ENTRYPOINT ["dotnet", "BibleApi.dll"]
```

### New docker-compose.yml:
```yaml
version: '3.9'

services:
  bible-api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ASPNETCORE_ENVIRONMENT=Development
      - AppSettings__AzureStorageConnectionString=${AZURE_STORAGE_CONNECTION_STRING}
      - AppSettings__AzureContainerName=bible-translations
    networks:
      - bible-network
    depends_on:
      - redis
      - sqlserver
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - bible-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  sqlserver:
    image: mcr.microsoft.com/mssql/server:2022-latest
    ports:
      - "1433:1433"
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=YourStrong@Passw0rd
      - MSSQL_PID=Developer
    volumes:
      - sqlserver-data:/var/opt/mssql
      - ./infrastructure/sql:/docker-entrypoint-initdb.d
    networks:
      - bible-network
    healthcheck:
      test: /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P YourStrong@Passw0rd -Q "SELECT 1"
      interval: 10s
      timeout: 5s
      retries: 10

  swagger-ui:
    image: swaggerapi/swagger-ui
    ports:
      - "8080:8080"
    environment:
      - SWAGGER_JSON=/api/swagger/v1/swagger.json
      - API_URL=http://bible-api:8000/swagger/v1/swagger.json
    networks:
      - bible-network

networks:
  bible-network:
    driver: bridge

volumes:
  sqlserver-data:
```

### .dockerignore Update:
```
**/.git
**/.gitignore
**/.vs
**/.vscode
**/bin
**/obj
**/out
**/*.md
**/Dockerfile*
**/docker-compose*
**/node_modules
**/.env
**/secrets.json
infrastructure/terraform/.terraform
infrastructure/terraform/*.tfstate*
```

---

## 📁 TASK 6: RESTRUCTURE SOLUTION (30 minutes)

### Update Solution File:
```xml
Microsoft Visual Studio Solution File, Format Version 12.00
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "BibleApi", "src\BibleApi\BibleApi.csproj"
EndProject
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "BibleApi.Tests", "tests\BibleApi.Tests\BibleApi.Tests.csproj"
EndProject
Global
  GlobalSection(SolutionConfigurationPlatforms) = preSolution
    Debug|Any CPU = Debug|Any CPU
    Release|Any CPU = Release|Any CPU
  EndGlobalSection
  ...
EndGlobal
```

### Update Project References:
All paths updated to new structure

---

## ✅ TASK 7: VERIFICATION & TESTING (30 minutes)

### Verification Steps:
1. ✅ Build solution: `dotnet build`
2. ✅ Run tests: `dotnet test`
3. ✅ Build Docker image: `docker build -f docker/Dockerfile -t bible-api:latest .`
4. ✅ Run docker-compose: `docker-compose up`
5. ✅ Test API endpoints: `curl http://localhost:8000/v1/data`
6. ✅ Verify Terraform: `terraform plan`
7. ✅ Check health endpoint: `curl http://localhost:8000/healthz`

---

## 📊 FINAL STRUCTURE

```
bible_api/
├── .git/
├── .github/
├── .gitignore
├── .dockerignore
├── BibleApi.sln                    # Updated solution
├── README.md                        # Updated
├── LICENSE
├── NOTICE
├── src/
│   └── BibleApi/
│       ├── BibleApi.csproj         # .NET 9
│       ├── Program.cs              # Modernized
│       ├── appsettings.json
│       ├── appsettings.Development.json
│       ├── wwwroot/
│       │   └── favicon.svg
│       ├── Controllers/
│       │   └── BibleController.cs
│       ├── Services/
│       │   ├── IAzureXmlBibleService.cs
│       │   ├── AzureXmlBibleService.cs
│       │   ├── CachedBibleService.cs
│       │   └── MockAzureXmlBibleService.cs
│       ├── Models/
│       │   └── BibleModels.cs
│       ├── Core/
│       │   ├── BookMetadata.cs
│       │   └── BibleConstants.cs
│       └── Configuration/
│           └── AppSettings.cs
├── tests/
│   └── BibleApi.Tests/
│       ├── BibleApi.Tests.csproj   # .NET 9
│       ├── BookMetadataTests.cs
│       └── BibleConstantsTests.cs
├── docker/
│   ├── Dockerfile                  # .NET 9
│   ├── docker-compose.yml          # Full stack
│   └── .env.example
├── infrastructure/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfvars.example
│   │   ├── modules/
│   │   │   ├── app-service/
│   │   │   ├── blob-storage/
│   │   │   └── sql-database/
│   │   └── README.md
│   └── sql/
│       ├── db_creation_script.sql
│       └── 20250919_use_verseid_fulltext.sql
└── docs/
    ├── CODE_ANALYSIS_REPORT.md
    ├── IMPLEMENTATION_PLAN.md
    ├── PHASE_0_PLAN.md
    ├── DATA_LICENSES.md
    └── API_GUIDE.md (to be created)
```

---

## 📋 EXECUTION CHECKLIST

### Preparation (5 min)
- [ ] Commit current state
- [ ] Create new branch: `phase-0/modernize-and-restructure`
- [ ] Backup important files

### Task 1: Remove BibleImporter (30 min)
- [ ] Delete BibleImporter folder
- [ ] Update BibleApi.sln
- [ ] Update Dockerfile
- [ ] Test build

### Task 2: Clean Up Structure (30 min)
- [ ] Create new folder structure
- [ ] Move BibleApi to src/
- [ ] Move BibleApi.Tests to tests/
- [ ] Move static files to wwwroot/
- [ ] Create infrastructure/ folder
- [ ] Move sql files
- [ ] Update all paths

### Task 3: Upgrade to .NET 9 (1 hour)
- [ ] Update BibleApi.csproj to net9.0
- [ ] Update BibleApi.Tests.csproj to net9.0
- [ ] Update package references
- [ ] Modernize Program.cs
- [ ] Apply primary constructors (optional)
- [ ] Test build and run

### Task 4: Create Terraform IaC (2-3 hours)
- [ ] Create infrastructure/terraform/ structure
- [ ] Write main.tf
- [ ] Write variables.tf
- [ ] Write outputs.tf
- [ ] Create modules
- [ ] Write README
- [ ] Test terraform init/plan

### Task 5: Modernize Docker (1 hour)
- [ ] Create docker/ folder
- [ ] Write new Dockerfile for .NET 9
- [ ] Write comprehensive docker-compose.yml
- [ ] Update .dockerignore
- [ ] Test Docker build

### Task 6: Update Solution (30 min)
- [ ] Update BibleApi.sln paths
- [ ] Remove phantom project references
- [ ] Test solution build

### Task 7: Verification (30 min)
- [ ] Build solution
- [ ] Run tests
- [ ] Build Docker image
- [ ] Run docker-compose
- [ ] Test API
- [ ] Verify Terraform

### Documentation (30 min)
- [ ] Update README.md
- [ ] Update .gitignore
- [ ] Create docs/DEPLOYMENT.md
- [ ] Commit and push

---

## ⏱️ ESTIMATED TIME: 6-7 hours (1 day)

With automation: **2-3 hours**

---

## 🚀 READY TO EXECUTE?

**Command to start**: `"Execute Phase 0"`

This will:
1. Remove BibleImporter
2. Restructure the project
3. Upgrade to .NET 9
4. Create Terraform IaC
5. Modernize Docker setup
6. Update documentation

**Alternatively**, execute tasks individually:
- `"Execute Phase 0 Task 1"` - Remove BibleImporter only
- `"Execute Phase 0 Task 2"` - Restructure only
- etc.

---

**Your command**: _______________________
