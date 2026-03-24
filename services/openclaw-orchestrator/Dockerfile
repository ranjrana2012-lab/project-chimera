FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY services/openclaw-orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/openclaw-orchestrator/ . .

# Copy shared module
COPY services/shared/ /app/shared/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
