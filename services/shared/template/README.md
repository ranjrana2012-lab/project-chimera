# Service Template

Production-ready service template for Project Chimera.

## Features

- FastAPI with async support
- OpenTelemetry tracing (Jaeger)
- Prometheus metrics
- Health checks
- ARM64 Docker support
- Comprehensive tests
- Environment-based configuration
- Pydantic models for validation

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
uvicorn main:app --reload --port 8000

# Run tests
pytest tests/ -v

# Build Docker image
docker build -t service-template .

# Run in Docker
docker run -p 8000:8000 service-template
```

## Environment Variables

The service supports the following environment variables (see `config.py`):

### Service Configuration
- `SERVICE_NAME`: Service name (default: "service-template")
- `SERVICE_VERSION`: Service version (default: "1.0.0")
- `PORT`: Port to listen on (default: 8000)
- `DEBUG`: Enable debug mode (default: false)
- `LOG_LEVEL`: Logging level (default: "INFO")

### OpenTelemetry
- `OTLP_ENDPOINT`: OTLP endpoint for tracing (default: "http://localhost:4317")

### Redis
- `REDIS_HOST`: Redis host (default: "localhost")
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_DB`: Redis database (default: 0)

### Kafka
- `KAFKA_BROKERS`: Kafka brokers (default: "localhost:9092")
- `KAFKA_TOPIC`: Kafka topic (default: "chimera-events")

### AI Models
- `GLM_API_KEY`: GLM API key (optional)
- `GLM_API_BASE`: GLM API base URL (default: "https://open.bigmodel.cn/api/paas/v4/")
- `LOCAL_MODEL_PATH`: Path to local model (optional)

## API Endpoints

### Health Checks

#### `GET /health/live`
Basic liveness check - is the process running?

**Response:**
```json
{
  "status": "alive"
}
```

#### `GET /health/ready`
Readiness check - can we handle requests?

**Response:**
```json
{
  "status": "ready",
  "checks": {}
}
```

### Metrics

#### `GET /metrics`
Prometheus metrics endpoint

**Response:** Prometheus text format

## Module Structure

```
template/
├── main.py          # FastAPI application
├── config.py        # Configuration management
├── models.py        # Pydantic models
├── metrics.py       # Prometheus metrics
├── tracing.py       # OpenTelemetry setup
├── tests/
│   ├── test_main.py # Health check tests
│   └── conftest.py  # Test fixtures
├── Dockerfile       # ARM64 Dockerfile
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## Usage as Template

To create a new service from this template:

1. Copy the template directory
2. Update `config.py` with service-specific configuration
3. Add business logic to `main.py`
4. Extend `models.py` with service-specific models
5. Customize `metrics.py` with business metrics
6. Update service name in `tracing.py` calls
7. Update Dockerfile and README.md

## Testing

The template includes TDD-style tests:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_main.py::test_health_live -v
```

## Docker

Build for ARM64:

```bash
docker build -t service-template .
```

Run container:

```bash
docker run -p 8000:8000 \
  -e LOG_LEVEL=DEBUG \
  -e OTLP_ENDPOINT=http://jaeger:4317 \
  service-template
```

## Observability

### Tracing

The template uses OpenTelemetry for distributed tracing. Spans are automatically:

- Created for each HTTP request
- Propagated to downstream services
- Exported to Jaeger via OTLP

To add custom span attributes:

```python
from tracing import add_span_attributes

add_span_attributes({"custom.attribute": "value"})
```

To record errors:

```python
from tracing import record_error

try:
    # Business logic
except Exception as e:
    record_error(e)
    raise
```

### Metrics

Prometheus metrics are exposed at `/metrics`:

- `http_requests_total`: Total HTTP requests (labels: method, endpoint, status)
- `http_request_duration_seconds`: Request duration (labels: method, endpoint)
- `business_operations_total`: Business operations (labels: operation, status)
- `service_info`: Service metadata (labels: name, version)

To record business metrics:

```python
from metrics import record_business_operation

record_business_operation("my_operation", "success")
```

## License

MIT License - see LICENSE file for details
