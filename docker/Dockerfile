#############################
# Bible API - .NET 9 Production Image
# Multi-stage build for optimized size
#############################

# Build stage
FROM mcr.microsoft.com/dotnet/sdk:9.0-alpine AS build
ARG BUILD_CONFIGURATION=Release
WORKDIR /src

# Copy solution and project files for better caching
COPY BibleApi.sln ./
COPY src/BibleApi/BibleApi.csproj src/BibleApi/
COPY tests/BibleApi.Tests/BibleApi.Tests.csproj tests/BibleApi.Tests/

# Restore dependencies
RUN dotnet restore BibleApi.sln

# Copy all source code
COPY src/ src/
COPY tests/ tests/

# Build the application
WORKDIR /src/src/BibleApi
RUN dotnet build BibleApi.csproj \
    -c $BUILD_CONFIGURATION \
    -o /app/build \
    --no-restore

# Publish the application
RUN dotnet publish BibleApi.csproj \
    -c $BUILD_CONFIGURATION \
    -o /app/publish \
    --no-restore \
    /p:UseAppHost=false

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:9.0-alpine AS runtime

# Install curl for health checks
RUN apk add --no-cache curl

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

WORKDIR /app

# Copy published application from build stage
COPY --from=build --chown=appuser:appgroup /app/publish .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Environment variables
ENV ASPNETCORE_URLS=http://+:8000 \
    ASPNETCORE_ENVIRONMENT=Production \
    DOTNET_RUNNING_IN_CONTAINER=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz || exit 1

# Entry point
ENTRYPOINT ["dotnet", "BibleApi.dll"]
