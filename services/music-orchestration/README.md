# Music Orchestration Service

Port 8012 - Caching, approval workflow, and show integration for music generation.

## Responsibilities
- Request routing and validation
- Exact-match caching (Redis)
- Staged approval pipeline
- Role-based access control
- Sentiment-based adaptive modulation
- WebSocket progress streaming

## Development

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## Running

```bash
uvicorn music_orchestration.main:app --host 0.0.0.0 --port 8012
```
