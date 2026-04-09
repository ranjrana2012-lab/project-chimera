# Visual Core Service Dockerfile
# Optimized for ARM64 (Nvidia DGX Spark GB10)
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (skip for now - using PyPI wheels)
# Note: ffmpeg will be mounted from host or added later if needed

# Set work directory
WORKDIR /app

# Copy shared requirements first
COPY services/shared/requirements.txt .
RUN pip install --no-cache-dir services/shared/requirements.txt

# Install Python dependencies
COPY services/visual-core/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/cache/videos /app/models/lora

# Copy application code
COPY services/visual-core/ . .

# Copy shared module
COPY services/shared/ /app/shared/

# Set Python path and port
ENV PYTHONPATH=/app
ENV PORT=8014

# Expose port
EXPOSE 8014

# Health check (use Python instead of curl)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8014/health/live')" || exit 1

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8014"]
