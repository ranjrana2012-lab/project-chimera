# Chimera Quality Platform

Unified testing and quality platform for Project Chimera.

## Overview

The Chimera Quality Platform is a custom-built testing infrastructure that orchestrates, executes, analyzes, and visualizes all testing across Project Chimera's 8 microservices.

## Services

- **Test Orchestrator** (port 8008) - Schedules and executes tests
- **Dashboard Service** (port 8009) - Real-time visualization
- **CI/CD Gateway** (port 8010) - GitHub/GitLab integration

## Quick Start

```bash
# Install dependencies
cd platform
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/chimera_quality"
export REDIS_URL="redis://localhost:6379/0"

# Run database migrations (create tables)
python -c "from platform.shared.database import engine, Base; import asyncio; asyncio.run(engine.connect());"

# Start services (in separate terminals)
uvicorn orchestrator.main:orchestrator_app --host 0.0.0.0 --port 8008
uvicorn dashboard.main:dashboard_app --host 0.0.0.0 --port 8009
uvicorn ci_gateway.main:ci_gateway_app --host 0.0.0.0 --port 8010

# Access dashboard
open http://localhost:8009
```

## Architecture

See [DESIGN.md](../docs/plans/2026-02-28-chimera-quality-platform-design.md) for detailed architecture.

## Features

- **Test Discovery** - Automatically finds all tests in the codebase
- **Parallel Execution** - Runs tests concurrently with resource management
- **Real-time Updates** - WebSocket streaming of test execution
- **Quality Gates** - Enforces coverage and mutation testing thresholds
- **CI/CD Integration** - GitHub and GitLab webhook support

## License

MIT
