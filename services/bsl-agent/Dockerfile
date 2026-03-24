# BSL Agent Dockerfile for ARM64 (Nvidia DGX Spark GB10)
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY services/bsl-agent/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/bsl-agent/*.py ./
COPY services/bsl-agent/tests/ ./tests/

# Copy shared module
COPY services/shared/ /app/shared/

# Create directory for avatar models (placeholder)
RUN mkdir -p /models/bsl_avatar

# Set environment variables
ENV PORT=8003 \
    LOG_LEVEL=INFO \
    ENVIRONMENT=production

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health/live')" || exit 1

# Run the application
CMD ["python", "main.py"]
