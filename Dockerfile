#############################
# Bible API - .NET Core Production Image
# Build: docker build -t bible-api:latest .
#############################

# Use the official .NET SDK image for building
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build

WORKDIR /src

# Copy csproj and restore dependencies
COPY BibleApi/BibleApi.csproj BibleApi/
RUN dotnet restore BibleApi/BibleApi.csproj

# Copy everything else and build
COPY BibleApi/ BibleApi/
WORKDIR /src/BibleApi
RUN dotnet build BibleApi.csproj -c Release -o /app/build

# Publish the application
RUN dotnet publish BibleApi.csproj -c Release -o /app/publish /p:UseAppHost=false

# Use the official .NET runtime image for running
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime

# Set environment variables
ENV ASPNETCORE_ENVIRONMENT=Production \
    ASPNETCORE_URLS=http://+:8000 \
    DOTNET_RUNNING_IN_CONTAINER=true

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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz || exit 1

# Default command
ENTRYPOINT ["dotnet", "BibleApi.dll"]