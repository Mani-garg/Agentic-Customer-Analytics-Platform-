# ==============================================================================
# Multi-stage Dockerfile for Agentic Customer Analytics Platform
# ==============================================================================

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY pyproject.toml .

# Install dependencies into wheels
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# ==============================================================================
# Final runtime stage
# ==============================================================================
FROM python:3.11-slim AS runtime

# System runtime dependencies & security setup
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --home-dir /home/appuser --shell /bin/bash appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source, configs, and scripts
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser scripts/ /app/scripts/
COPY --chown=appuser:appuser alembic.ini /app/
COPY --chown=appuser:appuser pyproject.toml /app/
COPY --chown=appuser:appuser .env.example /app/.env.example

# Set up runtime directories with correct permissions
RUN mkdir -p /app/data/raw /app/data/processed /app/data/sample /app/artifacts/models /app/artifacts/reports && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    APP_ENV=production \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# Expose HTTP port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Default startup command
CMD ["uvicorn", "customer_analytics.main:app", "--host", "0.0.0.0", "--port", "8000"]
