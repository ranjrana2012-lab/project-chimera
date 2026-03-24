FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY services/simulation-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY services/simulation-engine/ . .

# Expose port
EXPOSE 8016

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8016/health/live')" || exit 1

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8016"]
