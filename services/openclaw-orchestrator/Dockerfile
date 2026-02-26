# Multi-stage Dockerfile for OpenClaw Orchestrator
# Stage 1: Builder
FROM python:3.10-slim AS builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION=0.1.0
ARG VCS_REF

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim AS runtime

# Set build-time labels
LABEL maintainer="Project Chimera <project-chimera@university.ac.uk>" \
      org.opencontainers.image.title="OpenClaw Orchestrator" \
      org.opencontainers.image.description="Central control plane for Project Chimera" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.source="https://github.com/project-chimera/project-chimera" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_USER="chimera" \
    APP_DIR="/app"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r ${APP_USER} && \
    useradd -r -g ${APP_USER} -d ${APP_DIR} -s /sbin/nologin ${APP_USER}

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create application directory structure
RUN mkdir -p ${APP_DIR}/logs ${APP_DIR}/tmp && \
    chown -R ${APP_USER}:${APP_USER} ${APP_DIR}

# Set working directory
WORKDIR ${APP_DIR}

# Copy application code
COPY --chown=${APP_USER}:${APP_USER} src ./src

# Create necessary directories
RUN mkdir -p /app/skills /app/models /app/configs && \
    chown -R ${APP_USER}:${APP_USER} /app/skills /app/models /app/configs

# Switch to non-root user
USER ${APP_USER}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "openclaw_orchestrator.src.main"]
