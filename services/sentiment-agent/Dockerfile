# Sentiment Agent Dockerfile
# ARM64 optimized for Nvidia DGX Spark GB10

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY services/sentiment-agent/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download ML model (if needed during build)
RUN python3 -c 'from transformers import DistilBertTokenizer, DistilBertForSequenceClassification; import os; cache_dir = "./models_cache"; os.makedirs(cache_dir, exist_ok=True); print("Downloading DistilBERT model..."); DistilBertTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english", cache_dir=cache_dir); DistilBertForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english", cache_dir=cache_dir); print("Model downloaded successfully")'

# Copy source code
COPY services/sentiment-agent/src/ /app/src/

# Copy shared tracing module
COPY services/shared/ /app/shared/

# Set Python path
ENV PYTHONPATH=/app/src:/app

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8004/health/live')"

# Run the application
CMD ["python", "-m", "sentiment_agent.main"]
