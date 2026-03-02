# ADR-002: FastAPI for Microservices

## Status
Accepted

## Date
2026-02-26

## Context
Project Chimera requires a web framework for all microservices. Requirements include:
- Async/await support for I/O operations
- Type hints and validation
- OpenAPI documentation generation
- WebSocket support (for future real-time features)
- Performance comparable to Go

## Decision
Use **FastAPI** as the web framework for all Project Chimera services.

### Rationale

**Pros:**
- Native async/await with Python 3.10+
- Automatic OpenAPI documentation
- Pydantic for request/response validation
- Built-in dependency injection
- Excellent performance (comparable to Node.js/Go for I/O-bound workloads)
- WebSocket and SSE support
- Easy testing with pytest-asyncio

**Cons:**
- Python GIL affects CPU-bound tasks (mitigated by using external services)
- Async ecosystem can be complex (mitigated by using httpx)

## Consequences

- All services share consistent code patterns
- Type safety reduces runtime errors
- Auto-generated API documentation
- Team leverages existing Python knowledge
