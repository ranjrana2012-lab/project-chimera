# Multi-stage Dockerfile for Lighting Control
FROM python:3.10-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

FROM python:3.10-slim AS runtime

LABEL maintainer="Project Chimera <project-chimera@university.ac.uk>" \
      org.opencontainers.image.title="Lighting Control" \
      org.opencontainers.image.description="DMX lighting control service for stage lighting"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_USER="chimera" \
    APP_DIR="/app"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r ${APP_USER} && \
    useradd -r -g ${APP_USER} -d ${APP_DIR} -s /sbin/nologin ${APP_USER}

COPY --from=builder /opt/venv /opt/venv

RUN mkdir -p ${APP_DIR}/logs ${APP_DIR}/tmp && \
    chown -R ${APP_USER}:${APP_USER} ${APP_DIR}

WORKDIR ${APP_DIR}

COPY --chown=${APP_USER}:${APP_USER} src ./src

RUN mkdir -p /app/configs && \
    chown -R ${APP_USER}:${APP_USER} /app/configs

USER ${APP_USER}

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8005/health/live || exit 1

EXPOSE 8005

CMD ["python", "-m", "lighting_control.src.main"]
