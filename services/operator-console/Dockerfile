FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy shared requirements first
COPY services/shared/requirements.txt .
RUN pip install --no-cache-dir services/shared/requirements.txt

COPY services/operator-console/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/operator-console/*.py ./

# Copy shared module
COPY services/shared/ /app/shared/

RUN mkdir -p static
COPY services/operator-console/static/ ./static/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8007

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8007/health/live')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
