#############################
# Bible API - .NET Core Production Image
# Build: docker build -t bible-api:latest .
#############################

# Use the official .NET SDK image for building
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build

WORKDIR /src

# Copy solution and project files for better layer caching
COPY BibleApi.sln ./
COPY BibleApi/BibleApi.csproj BibleApi/
COPY BibleApi.Tests/BibleApi.Tests.csproj BibleApi.Tests/
COPY BibleImporter/BibleImporter.csproj BibleImporter/

# Restore dependencies for all projects
RUN dotnet restore BibleApi.sln

# Copy source files and build
COPY BibleApi/ BibleApi/
COPY BibleApi.Tests/ BibleApi.Tests/
COPY BibleImporter/ BibleImporter/

WORKDIR /src/BibleApi
RUN dotnet build BibleApi.csproj -c Release -o /app/build --no-restore

# Publish the application
RUN dotnet publish BibleApi.csproj -c Release -o /app/publish /p:UseAppHost=false --no-restore

# Use the official .NET runtime image for running
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime

# Set environment variables for optimization
ENV ASPNETCORE_ENVIRONMENT=Production \
    ASPNETCORE_URLS=http://+:8000 \
    DOTNET_RUNNING_IN_CONTAINER=true \
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=true \
    DOTNET_USE_POLLING_FILE_WATCHER=true \
    ASPNETCORE_FORWARDEDHEADERS_ENABLED=true

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --system --create-home --uid 1001 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Copy published application
COPY --from=build /app/publish .

EXPOSE 8000

# Enhanced health check with better timeout and failure handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz --max-time 8 || exit 1

# Default command
ENTRYPOINT ["dotnet", "BibleApi.dll"]