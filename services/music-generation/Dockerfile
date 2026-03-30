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
    curl \
    make \
    cmake \
    pkg-config \
    libsentencepiece-dev \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Set compiler environment variables for building
ENV CC=gcc \
    CXX=g++ \
    CMAKE_MAKE_PROGRAM=make

# Copy shared requirements first
COPY services/shared/requirements.txt .
RUN pip install --no-cache-dir services/shared/requirements.txt

# Copy requirements first for better caching
COPY services/music-generation/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/music-generation/*.py ./
COPY services/music-generation/tests/ ./tests/

# Copy shared module
COPY services/shared/ /app/shared/

# Create directory for models
RUN mkdir -p /models/musicgen /models/acestep /models/cache

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

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
