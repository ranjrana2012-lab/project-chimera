# Music Generation Service Dockerfile for ARM64 (Nvidia DGX Spark GB10)
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TORCH_CUDA_ARCH_LIST="8.0+PTX" \
    FORCE_CUDA="1"

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing and ML
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    cmake \
    pkg-config \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./
COPY tests/ ./tests/

# Create directory for models
RUN mkdir -p /models/musicgen /models/acestep /models/cache

# Set environment variables
ENV PORT=8011 \
    LOG_LEVEL=INFO \
    ENVIRONMENT=production \
    DEVICE=cuda

# Expose port
EXPOSE 8011

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8011/health/live')" || exit 1

# Run the application
CMD ["python", "main.py"]
