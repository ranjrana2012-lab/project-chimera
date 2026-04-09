# Chimera Simulation Engine

A multi-agent swarm intelligence simulation platform for "what-if" scenario testing.

## Architecture

Five-stage pipeline:
1. Knowledge Graph Construction (GraphRAG-inspired)
2. Environment Setup (Agent Persona Generation)
3. Simulation Execution (OASIS-inspired)
4. Report Generation (ReACT-pattern)
5. Deep Interaction (Agent Query)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run tests
pytest tests/ -v

# Start server
python main.py
```

## API Endpoints

- `POST /api/v1/graph/build` - Build knowledge graph from documents
- `POST /api/v1/agents/generate` - Generate agent personas
- `POST /api/v1/simulation/simulate` - Run simulation
- `GET /health/live` - Health check
- `GET /metrics` - Prometheus metrics

## Cost Control

Tiered LLM routing:
- 95% local vLLM (Llama 3 8B) - ~$0
- 5% API (Claude/GPT-4) - ~$0.01 per simulation

## License

MIT/Apache-2.0 (permissive)
