#############################
# Bible API - Production Image
# Build: docker build -t bible-api:latest .
#############################
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UVICORN_WORKERS=1 \
    PORT=8000

WORKDIR /app

# Install minimal system dependencies (curl for health + diagnostics)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip explicitly (security, speed)
RUN pip install --upgrade pip

# Copy requirements first for caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create non-root user (no shell needed in container runtime)
RUN useradd --system --create-home --uid 1001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check (basic). For more robust readiness, add a /healthz route.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -fsS http://localhost:${PORT}/healthz || curl -fsS http://localhost:${PORT}/ || exit 1

# Default command (single worker). Scale via orchestrator, not in-process.
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# (Optional) Multi-stage optimization suggestion:
# Use a builder stage to precompile wheels if heavy dependencies are added later.