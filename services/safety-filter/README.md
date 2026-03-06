# Safety Filter

Multi-layer content moderation service ensuring family-friendly output for Project Chimera.

## Overview

The Safety Filter provides comprehensive content moderation:
- Word-based profanity filtering
- ML-based offensive content detection (optional)
- Context-aware policy enforcement
- Audit logging for all filtered content
- Multiple policy levels (family, teen, adult)

## Quick Start

```bash
# Prerequisites
# - Python 3.10+
# - Optional: ML model for enhanced filtering

# Local development setup
cd services/safety-filter
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your policy preferences

# Run service
uvicorn main:app --reload --port 8006
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `safety-filter` | Service identifier |
| `PORT` | `8006` | HTTP server port |
| `DEFAULT_POLICY` | `family` | Default moderation policy |
| `ENABLE_ML_FILTER` | `false` | Enable ML-based filtering |
| `ENABLE_CONTEXT_FILTER` | `true` | Enable context-aware filtering |
| `CACHE_TTL` | `3600` | Filter cache TTL (seconds) |
| `AUDIT_LOG_MAX_SIZE` | `10000` | Max audit log entries |
| `AUDIT_LOG_RETENTION_HOURS` | `24` | Audit log retention |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks word lists)
- `GET /metrics` - Prometheus metrics

### Content Filtering
- `POST /api/v1/filter` - Filter content for policy violations
- `POST /api/v1/check` - Check content without filtering
- `GET /api/v1/policies` - List available policies
- `GET /api/v1/audit` - Get audit log

**Example: Filter content**
```bash
curl -X POST http://localhost:8006/api/v1/filter \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your text here",
    "policy": "family"
  }'
```

**Response (safe):**
```json
{
  "safe": true,
  "content": "Your text here",
  "filtered": false,
  "reason": null
}
```

**Response (unsafe):**
```json
{
  "safe": false,
  "content": "*** text here",
  "filtered": true,
  "reason": "profanity_detected",
  "violations": ["word_list"]
}
```

## Development

### Code Structure
```
safety-filter/
├── main.py              # FastAPI application
├── word_filter.py       # Word-based filtering
├── ml_filter.py         # ML-based filtering (optional)
├── context_filter.py    # Context-aware filtering
├── audit_logger.py      # Audit log management
├── cache.py            # Filter result cache
├── config.py           # Configuration
├── models.py           # Pydantic models
├── metrics.py          # Prometheus metrics
├── tracing.py          # OpenTelemetry setup
└── tests/              # Test suite
```

### Adding Features
1. Add new policy levels in `word_filter.py`
2. Implement new ML models in `ml_filter.py`
3. Add context rules in `context_filter.py`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_filter.py -v
```

## Troubleshooting

### Over-Filtering Content
**Symptom:** Safe content being blocked
**Solution:** Adjust `DEFAULT_POLICY`, review word lists, check context rules

### Under-Filtering Content
**Symptom:** Unsafe content not caught
**Solution:** Enable `ENABLE_ML_FILTER`, update word lists, add context rules

### Audit Log Growing Too Large
**Symptom:** High disk usage
**Solution:** Reduce `AUDIT_LOG_RETENTION_HOURS`, decrease `AUDIT_LOG_MAX_SIZE`

## Contributing

Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT - Project Chimera
