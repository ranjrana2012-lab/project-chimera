# Dockerfile for Lighting-Sound-Music Service
# ARM64-optimized for Nvidia DGX Spark GB10

FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    portaudio19-dev \
    python3-dev \
    libsdl2-dev \
    libsdl2-mixer-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy shared requirements first
COPY services/shared/requirements.txt .
RUN pip install --no-cache-dir services/shared/requirements.txt

# Copy requirements first for better caching
COPY services/lighting-sound-music/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY services/lighting-sound-music/ . .

# Copy shared module
COPY services/shared/ /app/shared/

# Create non-root user (already there)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/health/live')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
