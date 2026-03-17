# API Endpoints Reference

Complete API endpoint reference for the Chimera Simulation Engine.

> **Implementation Status**: This documentation reflects the current implementation (v0.1.0). Some endpoints documented under "Planned Features" are not yet implemented but are included for future reference.

## Base URLs

- **Development**: `http://localhost:8016`
- **Production**: `http://simulation-engine:8016`
- **Interactive API Docs**: `http://localhost:8016/docs` (Swagger UI)
- **Alternative API Docs**: `http://localhost:8016/redoc` (ReDoc)

## Authentication

Currently, the Simulation Engine does not require authentication. This may change in future versions.

## Response Format

All endpoints return JSON responses with appropriate HTTP status codes.

## Status Codes

| Code | Description |
|------|-------------|
| `200` | Success - Request completed successfully |
| `400` | Bad Request - Invalid request parameters |
| `422` | Validation Error - Request body validation failed |
| `500` | Internal Server Error - Unexpected server error |
| `503` | Service Unavailable - Required service not initialized |

---

## Health Endpoints

### GET /health/live

Liveness probe - checks if the service is running.

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "service": "simulation-engine",
  "version": "0.1.0"
}
```

**Example**:

```bash
curl -X GET http://localhost:8016/health/live
```

---

### GET /health/ready

Readiness probe - checks if the service can accept requests.

**Response**: `200 OK`

```json
{
  "status": "ready",
  "service": "simulation-engine",
  "version": "0.1.0"
}
```

**Example**:

```bash
curl -X GET http://localhost:8016/health/ready
```

---

## Knowledge Graph Endpoints

### POST /api/v1/graph/build

Build a knowledge graph from documents using entity and relationship extraction.

**Request Body**:

```json
{
  "documents": [
    "Document text 1...",
    "Document text 2..."
  ]
}
```

**Response**: `200 OK`

```json
{
  "graph_id": "temp_graph_1",
  "entities": 42,
  "relationships": 38
}
```

**Error Response**: `503 Service Unavailable`

```json
{
  "detail": "Graph service not initialized"
}
```

**Example**:

```bash
curl -X POST http://localhost:8016/api/v1/graph/build \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      "The immune system protects the body from infection.",
      "White blood cells are a key component of immune response."
    ]
  }'
```

---

## Simulation Endpoints

### POST /api/v1/simulation/simulate

Start a new multi-agent simulation with the specified configuration.

**Request Body**:

```json
{
  "agent_count": 10,
  "simulation_rounds": 10,
  "scenario_description": "Discuss the implications of AI in healthcare",
  "scenario_topic": "AI in Healthcare",
  "seed_documents": [
    "AI has the potential to revolutionize medical diagnosis...",
    "Machine learning algorithms can analyze medical images..."
  ],
  "generate_report": false
}
```

**Request Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_count` | integer | Yes | Number of agents (1-1000) |
| `simulation_rounds` | integer | Yes | Number of simulation rounds (1-100) |
| `scenario_description` | string | Yes | Description of the scenario |
| `scenario_topic` | string | No | Optional topic for the scenario |
| `seed_documents` | array | No | Optional seed documents for context |
| `generate_report` | boolean | No | Whether to generate a report (default: false) |

**Response**: `200 OK`

```json
{
  "simulation_id": "sim_1234567890",
  "status": "completed",
  "rounds_completed": 10,
  "total_actions": 87,
  "summary": "Simulation completed with diverse agent perspectives..."
}
```

**Error Response**: `503 Service Unavailable`

```json
{
  "detail": "Simulation service not initialized"
}
```

**Example**:

```bash
curl -X POST http://localhost:8016/api/v1/simulation/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 25,
    "simulation_rounds": 15,
    "scenario_description": "Debate the ethics of autonomous vehicles",
    "scenario_topic": "Ethics of AI",
    "generate_report": true
  }'
```

---

## Agent Endpoints

### POST /api/v1/agents/generate

Generate agent personas for use in simulations.

**Request Body**:

```json
{
  "count": 10,
  "seed": 42
}
```

**Request Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `count` | integer | Yes | Number of personas to generate (1-1000) |
| `seed` | integer | No | Random seed for reproducibility |

**Response**: `200 OK`

```json
{
  "personas": [
    {
      "agent_id": "agent_001",
      "name": "Dr. Sarah Chen",
      "age": 34,
      "occupation": "Healthcare Researcher",
      "personality_traits": ["analytical", "empathetic", "cautious"],
      "background": "PhD in Biomedical Engineering with 10 years of experience...",
      "perspectives": {
        "primary": "Evidence-based approach to AI adoption",
        "secondary": "Patient safety first"
      }
    }
  ],
  "count": 10
}
```

**Error Response**: `400 Bad Request`

```json
{
  "detail": "Count must be between 1 and 1000"
}
```

**Example**:

```bash
curl -X POST http://localhost:8016/api/v1/agents/generate \
  -H "Content-Type: application/json" \
  -d '{
    "count": 25,
    "seed": 123
  }'
```

---

## Agent Interaction Endpoints

> **Note**: Agent interaction endpoints are planned for future implementation.

### POST /api/v1/agent/{agent_id}/interview

> **Status**: Planned - Not yet implemented

Conduct an interview with a specific agent to understand their perspective.

**URL Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Unique identifier of the agent |

**Request Body**:

```json
{
  "questions": [
    "What is your perspective on AI in healthcare?",
    "What concerns do you have about autonomous systems?"
  ],
  "context": "Discussing ethics of AI deployment"
}
```

**Request Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `questions` | array | Yes | List of questions to ask the agent |
| `context` | string | No | Optional context for the interview |

**Response**: `200 OK`

```json
{
  "agent_id": "agent_001",
  "interview_id": "interview_abc123",
  "responses": [
    {
      "question": "What is your perspective on AI in healthcare?",
      "answer": "Based on my experience in healthcare research...",
      "confidence": 0.87,
      "reasoning": "My perspective is shaped by..."
    }
  ],
  "timestamp": 1640995200.0
}
```

**Example**:

```bash
curl -X POST http://localhost:8016/api/v1/agent/agent_001/interview \
  -H "Content-Type: application/json" \
  -d '{
    "questions": [
      "How do you think AI will change your field in the next 5 years?"
    ],
    "context": "Future of healthcare technology"
  }'
```

---

## Reporting Endpoints

> **Note**: Reporting endpoints are planned for future implementation.

### POST /api/v1/report/generate

> **Status**: Planned - Not yet implemented

Generate a comprehensive report from simulation results.

**Request Body**:

```json
{
  "simulation_id": "sim_1234567890",
  "report_type": "comprehensive",
  "include_analysis": true,
  "include_recommendations": true,
  "format": "markdown"
}
```

**Request Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `simulation_id` | string | Yes | ID of the simulation to report on |
| `report_type` | string | No | Type of report (default: "comprehensive") |
| `include_analysis` | boolean | No | Include detailed analysis |
| `include_recommendations` | boolean | No | Include recommendations |
| `format` | string | No | Output format (markdown, json, html) |

**Response**: `200 OK`

```json
{
  "report_id": "report_xyz789",
  "simulation_id": "sim_1234567890",
  "report_type": "comprehensive",
  "content": "# Simulation Report\n\n## Executive Summary\n\n...",
  "metadata": {
    "generated_at": 1640995800.0,
    "word_count": 1250,
    "sections": ["Executive Summary", "Analysis", "Recommendations"]
  }
}
```

**Example**:

```bash
curl -X POST http://localhost:8016/api/v1/report/generate \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_id": "sim_1234567890",
    "report_type": "comprehensive",
    "include_analysis": true,
    "format": "markdown"
  }'
```

---

## Metrics Endpoints

### GET /metrics

Prometheus metrics endpoint for monitoring and observability.

**Response**: `200 OK`

```
# HELP simulations_total Total number of simulations started
# TYPE simulations_total counter
simulations_total{scenario_type="healthcare"} 42.0
simulations_total{scenario_type="ethics"} 15.0

# HELP simulation_duration_seconds Simulation execution time
# TYPE simulation_duration_seconds histogram
simulation_duration_seconds_bucket{scenario_type="healthcare",le="0.1"} 5.0
simulation_duration_seconds_bucket{scenario_type="healthcare",le="0.5"} 23.0
simulation_duration_seconds_bucket{scenario_type="healthcare",le="1.0"} 42.0
simulation_duration_seconds_sum{scenario_type="healthcare"} 18.7
simulation_duration_seconds_count{scenario_type="healthcare"} 42.0
```

**Example**:

```bash
curl -X GET http://localhost:8016/metrics
```

---

## Error Handling

All endpoints follow a consistent error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Scenarios

1. **Service Not Initialized (503)**: Returned when a required service component hasn't been initialized
2. **Invalid Parameters (400)**: Returned when request parameters are invalid
3. **Validation Errors (422)**: Returned when request body fails validation
4. **Internal Server Error (500)**: Returned for unexpected server errors

---

## Rate Limiting

Currently, there are no rate limits enforced on the API. This may change in production deployments.

---

## Versioning

The current API version is `v1`. All endpoints are prefixed with `/api/v1/` except for health and metrics endpoints.

API versioning follows semantic versioning. Breaking changes will result in a new major version (e.g., `/api/v2/`).

---

## Interactive Documentation

For interactive API documentation with the ability to test endpoints directly:

- **Swagger UI**: `http://localhost:8016/docs`
- **ReDoc**: `http://localhost:8016/redoc`

These interfaces provide detailed schema information and allow you to make requests directly from the browser.

---

## WebSocket Support

WebSocket support for real-time simulation updates is planned for future releases.

---

## SDKs and Client Libraries

Official SDKs are planned for the following languages:

- Python
- JavaScript/TypeScript
- Go

Check the [Getting Started Guide](../getting-started/quick-start.md) for the latest availability information.

---

## Related Documentation

- **API Models Reference** (coming soon) - Detailed data model documentation
- **Usage Examples** (coming soon) - Practical API usage examples
- **Architecture Documentation** (coming soon) - System architecture overview
- **Running Simulations Guide** (coming soon) - Complete simulation guide
- **Getting Started Guide** (coming soon) - Quick start and installation guide

---

## Planned Features

The following endpoints are planned for future releases:

- **Simulation Status & Results**: GET endpoints to query simulation status and retrieve results
- **Agent Interaction**: Interview endpoints for deep agent interaction
- **Reporting**: Comprehensive report generation from simulation results
- **WebSocket Support**: Real-time simulation updates
- **Authentication**: API authentication and authorization
- **Rate Limiting**: Production-ready rate limiting

Check the [Project Roadmap](https://github.com/your-org/chimera/blob/main/docs/ROADMAP.md) for implementation timelines.
