# Safety Filter Service
# Multi-layer content moderation for AI-generated content
# Optimized with multi-stage build and production dependencies only

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Add Python path for shared module imports
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies and cleanup in single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user first (before copying code to avoid large layer)
RUN useradd -m -u 1000 appuser

# Copy shared requirements first
COPY services/shared/requirements.txt ./shared_requirements.txt

# Copy only production requirements (excluding test dependencies)
COPY services/safety-filter/requirements.txt .

# Filter out test dependencies and install
RUN grep -v "pytest\|httpx" requirements.txt > /tmp/requirements_prod.txt 2>/dev/null || cp requirements.txt /tmp/requirements_prod.txt && \
    pip install --no-cache-dir -r /tmp/requirements_prod.txt && \
    pip install --no-cache-dir -r shared_requirements.txt && \
    rm /tmp/requirements_prod.txt

# Copy application code
COPY services/safety-filter/*.py ./

# Copy shared module
COPY services/shared/ /app/shared/

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/health/live')"

# Run the application
CMD ["python", "main.py"]
