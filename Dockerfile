# 🧠 QUANTUM MEMORY ORCHESTRATOR - PRODUCTION DOCKERFILE
# Case: 1FDV-23-0001009
# BAMCPAPIN High Power Architecture
# Multi-stage build for optimal performance

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION=1.0.0-PRODUCTION
ARG CASE_ID=1FDV-23-0001009

# Labels for metadata
LABEL maintainer="GlacierEQ <glacier.equilibrium@gmail.com>" \
      version="${VERSION}" \
      case.id="${CASE_ID}" \
      build.date="${BUILD_DATE}" \
      description="Quantum Memory Orchestrator - Production System"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create application directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r quantum && useradd -r -g quantum quantum

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/config /app/src /app/tests \
    && chown -R quantum:quantum /app

# Copy application code
COPY --chown=quantum:quantum . /app/

# Set Python path
ENV PYTHONPATH=/app

# Environment variables for production
ENV ENVIRONMENT=production \
    CASE_ID=1FDV-23-0001009 \
    ORG_ID=case-1fdv-23-0001009 \
    PORT=8000 \
    HOST=0.0.0.0 \
    WORKERS=4 \
    LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER quantum

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "-m", "uvicorn", "src.orchestrator.quantum_memory:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Alternative production command with Gunicorn
# CMD ["gunicorn", "src.orchestrator.quantum_memory:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]