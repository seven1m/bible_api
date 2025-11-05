# Bible API - Docker Setup

This directory contains Docker configuration for running the Bible API locally and in production.

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) >= 20.10
- [Docker Compose](https://docs.docker.com/compose/install/) >= 2.0

### Run Locally

```bash
# From the project root
cd docker
docker-compose up
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/swagger
- **Standalone Swagger**: http://localhost:8080
- **Database Admin (Adminer)**: http://localhost:8081
- **Redis Commander**: http://localhost:8082

## Services

### Bible API (Port 8000)

Main ASP.NET Core Web API application.

**Health Check**: http://localhost:8000/healthz

**Environment Variables**:
- `ASPNETCORE_ENVIRONMENT` - Environment name (Development/Staging/Production)
- `AppSettings__AzureStorageConnectionString` - Azure Blob Storage connection
- `ConnectionStrings__BibleDatabase` - SQL Server connection string
- `ConnectionStrings__Redis` - Redis connection string

### Redis (Port 6379)

In-memory cache for improved performance.

**Configuration**:
- Max memory: 256MB
- Eviction policy: allkeys-lru
- Persistence: AOF enabled

**Redis Commander**: http://localhost:8082

### SQL Server (Port 1433)

Microsoft SQL Server for Bible verse storage.

**Credentials**:
- Server: localhost,1433
- Username: sa
- Password: YourStrong@Passw0rd (change in production!)
- Database: BibleDb

**Adminer UI**: http://localhost:8081

### Azurite (Ports 10000-10002)

Azure Storage Emulator for local development.

**Connection String**:
```
UseDevelopmentStorage=true
```

Or connect to specific services:
- Blob: http://localhost:10000
- Queue: http://localhost:10001
- Table: http://localhost:10002

### Swagger UI (Port 8080)

Standalone Swagger UI for API documentation.

## Docker Commands

### Build and Run

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f bible-api

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Individual Services

```bash
# Start only specific services
docker-compose up bible-api redis

# Restart a service
docker-compose restart bible-api

# View service logs
docker-compose logs -f bible-api
```

### Development Workflow

```bash
# Rebuild after code changes
docker-compose up --build bible-api

# Execute commands in running container
docker-compose exec bible-api /bin/sh

# Check service health
docker-compose ps
```

## Production Build

### Build for Production

```bash
# Build production image
docker build -f Dockerfile -t bible-api:latest ..

# Tag for registry
docker tag bible-api:latest myregistry.azurecr.io/bible-api:v1.0.0

# Push to registry
docker push myregistry.azurecr.io/bible-api:v1.0.0
```

### Production docker-compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.9'

services:
  bible-api:
    image: myregistry.azurecr.io/bible-api:latest
    environment:
      - ASPNETCORE_ENVIRONMENT=Production
      - AppSettings__AzureStorageConnectionString=${AZURE_STORAGE_CONNECTION_STRING}
    ports:
      - "80:8000"
```

## Environment Variables

### Required

| Variable | Description | Default |
|----------|-------------|---------|
| `ASPNETCORE_ENVIRONMENT` | Environment name | Development |
| `AppSettings__AzureStorageConnectionString` | Azure Storage connection | UseDevelopmentStorage=true |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `ConnectionStrings__BibleDatabase` | SQL connection string | - |
| `ConnectionStrings__Redis` | Redis connection string | - |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | AppInsights connection | - |

## Volumes

Persistent data is stored in named volumes:

- `bible-sqlserver-data` - SQL Server database files
- `bible-redis-data` - Redis persistence files
- `bible-azurite-data` - Azurite storage files

### Backup Volumes

```bash
# Backup SQL Server data
docker run --rm \
  -v bible-sqlserver-data:/source:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/sqlserver-backup.tar.gz -C /source .

# Restore SQL Server data
docker run --rm \
  -v bible-sqlserver-data:/target \
  -v $(pwd):/backup \
  alpine tar xzf /backup/sqlserver-backup.tar.gz -C /target
```

## Networking

All services communicate through the `bible-network` bridge network.

**Service DNS Names**:
- bible-api
- redis
- sqlserver
- azurite

Example connection string from within the network:
```
Server=sqlserver;Database=BibleDb;User Id=sa;Password=...
```

## Troubleshooting

### API not starting

Check logs:
```bash
docker-compose logs bible-api
```

Common issues:
- Waiting for database: Check SQL Server health
- Connection refused: Ensure dependencies are healthy

### Database connection issues

```bash
# Test SQL Server connection
docker-compose exec sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P YourStrong@Passw0rd -Q "SELECT 1" -C

# Check health status
docker-compose ps
```

### Port already in use

```bash
# Find process using port
lsof -i :8000

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Clear all data

```bash
# Stop services and remove volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all -v
```

## Security Notes

⚠️ **Important for Production**:

1. Change default passwords
2. Use secrets management (Azure Key Vault, Docker Secrets)
3. Don't expose database ports publicly
4. Use HTTPS in production
5. Implement firewall rules
6. Regular security updates

## Performance Tuning

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  bible-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 512M
        reservations:
          cpus: '1'
          memory: 256M
```

### Health Check Tuning

Adjust based on your needs:

```yaml
healthcheck:
  interval: 60s      # Check less frequently
  timeout: 5s        # Shorter timeout
  retries: 3
  start_period: 30s  # App startup time
```

## Monitoring

### View Resource Usage

```bash
# All containers
docker stats

# Specific container
docker stats bible-api
```

### Export Logs

```bash
# Export to file
docker-compose logs > logs.txt

# Filter by service
docker-compose logs bible-api > api-logs.txt
```

## Support

For issues:
- Check service logs: `docker-compose logs <service>`
- Verify health: `docker-compose ps`
- Review environment: `docker-compose config`
