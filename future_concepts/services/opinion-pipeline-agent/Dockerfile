FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install shared requirements first
COPY services/shared/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install service dependencies
COPY services/opinion-pipeline-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/opinion-pipeline-agent/ . .

# Copy shared module
COPY services/shared/ /app/shared/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8020

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8020/health/live')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8020"]
