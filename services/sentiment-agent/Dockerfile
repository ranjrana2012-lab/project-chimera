# Sentiment Agent Dockerfile
# ARM64 optimized for Nvidia DGX Spark GB10

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared requirements first
COPY services/shared/requirements.txt ./shared_requirements.txt
RUN pip install --no-cache-dir -r shared_requirements.txt

# Copy requirements first for better caching
COPY services/sentiment-agent/requirements.txt .

# Install Python dependencies.
# The MVP compose profile is a CPU preview path, so skip the PyTorch wheel here
# and allow the service's built-in mock fallback to run when ML deps are absent.
RUN grep -v "^torch==" requirements.txt > /tmp/requirements_no_torch.txt && \
    pip install --no-cache-dir -r /tmp/requirements_no_torch.txt && \
    rm /tmp/requirements_no_torch.txt

# Create models cache directory (model will be downloaded at runtime)
RUN mkdir -p ./models_cache

# Copy source code
COPY services/sentiment-agent/src/ /app/src/

# Copy shared tracing module
COPY services/shared/ /app/shared/

# Set Python path
ENV PYTHONPATH=/app/src:/app

# Set HuggingFace cache directories
ENV HF_HUB_CACHE=/app/models_cache
ENV TRANSFORMERS_CACHE=/app/models_cache

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8004/health/live')" || exit 1

# Run the application
CMD ["python", "-m", "sentiment_agent.main"]
