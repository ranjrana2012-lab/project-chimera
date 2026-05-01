# Kimi K2.6 Super-Agent Container
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
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY services/kimi-super-agent/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/kimi-super-agent/ .

# Copy configuration
COPY config/kimi-super-agent/config.yaml /etc/kimi/config.yaml

# Set environment variables
ENV PYTHONPATH=/app \
    CHIMERA_RUNTIME_PROFILE=dgx-spark

# Expose gRPC port
EXPOSE 50052

# Health check - verify gRPC server is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import grpc; channel = grpc.insecure_channel('localhost:50052'); grpc.channel_ready_future(channel).result(timeout=5)" || exit 1

# Run the service
CMD ["python", "-m", "kimi_orchestrator"]
