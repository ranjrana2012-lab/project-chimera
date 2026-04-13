# SceneSpeak Agent Dockerfile
# Optimized for ARM64 architecture (Nvidia DGX Spark GB10)

FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install ARM64 dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Add Python path for shared module imports
ENV PYTHONPATH=/app:$PYTHONPATH

# Install dependencies
COPY services/scenespeak-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared security modules
COPY services/shared/requirements.txt ./shared_requirements.txt
RUN pip install --no-cache-dir -r shared_requirements.txt
COPY services/shared/ /app/shared/

# Copy application code
COPY services/scenespeak-agent/ . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose service port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health/live')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
