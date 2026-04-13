# Safety Filter Service
# Multi-layer content moderation for AI-generated content
# Note: Remove --platform flag for CI compatibility with x86_64 runners

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Add Python path for shared module imports
ENV PYTHONPATH=/app:$PYTHONPATH

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared requirements first
COPY services/shared/requirements.txt ./shared_requirements.txt
RUN pip install --no-cache-dir -r shared_requirements.txt

# Copy requirements first for better caching
COPY services/safety-filter/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/safety-filter/*.py ./

# Copy shared module
COPY services/shared/ /app/shared/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/health/live')"

# Run the application
CMD ["python", "main.py"]
