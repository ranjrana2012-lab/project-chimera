FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY music_orchestration/ ./music_orchestration/

# Expose port
EXPOSE 8012

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8012/health || exit 1

# Run application
CMD ["uvicorn", "music_orchestration.main:app", "--host", "0.0.0.0", "--port", "8012"]
