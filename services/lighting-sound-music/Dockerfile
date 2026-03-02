# Multi-stage Dockerfile for Lighting, Sound & Music Service
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install build dependencies for audio packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    curl \
    libsndfile1 \
    portaudio19-dev \
    libportmidi0 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

FROM python:3.12-slim AS runtime

LABEL maintainer="Project Chimera <project-chimera@university.ac.uk>" \
      org.opencontainers.image.title="Lighting, Sound & Music Service" \
      org.opencontainers.image.description="Unified service for stage lighting, sound effects, and music generation using ACE-Step 1.5"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_USER="chimera" \
    APP_DIR="/app"

# Install runtime dependencies for audio and lighting control
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libsndfile1 \
    libasound2 \
    libportaudio2 \
    libportmidi0 \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r ${APP_USER} && \
    useradd -r -g ${APP_USER} -d ${APP_DIR} -s /sbin/nologin ${APP_USER}

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create application directory structure
RUN mkdir -p ${APP_DIR}/logs ${APP_DIR}/tmp ${APP_DIR}/assets/sounds ${APP_DIR}/assets/music && \
    chown -R ${APP_USER}:${APP_USER} ${APP_DIR}

WORKDIR ${APP_DIR}

# Copy application code
COPY --chown=${APP_USER}:${APP_USER} main.py .

# TODO: Copy assets (will be populated in subsequent tasks)
# COPY --chown=${APP_USER}:${APP_USER} assets ./assets

# TODO: Copy models directory structure (will be populated in subsequent tasks)
# COPY --chown=${APP_USER}:${APP_USER} models ./models

# TODO: Copy ACE-Step library
# COPY --chown=${APP_USER}:${APP_USER} acestep-lib ./acestep-lib

USER ${APP_USER}

# Health check - service must respond within 10s
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8005/health/live || exit 1

# Expose service port
EXPOSE 8005

# Run application with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005", "--log-level", "info"]
