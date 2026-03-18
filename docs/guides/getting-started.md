# Getting Started with Chimera Simulation Engine

Get up and running with the Chimera Simulation Engine in under 15 minutes. This guide will walk you through installation, your first simulation, and verification steps.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11 or higher** - The simulation engine requires Python 3.11+
- **Docker and Docker Compose** - For running Neo4j and other dependencies (optional but recommended)
- **Git** - For cloning the repository
- **API Keys** (optional) - OpenAI and/or Anthropic API keys for enhanced LLM capabilities

### Checking Your Prerequisites

```bash
# Check Python version (must be 3.11+)
python --version

# Check Docker
docker --version
docker-compose --version

# Check Git
git --version
```

## Installation

### Option 1: Using Docker Compose (Recommended)

The easiest way to get started is with Docker Compose, which handles all dependencies automatically.

```bash
# Navigate to the simulation engine directory
cd /home/ranj/Project_Chimera/services/simulation-engine

# Start all services (Neo4j, PostgreSQL, vLLM, Simulation Engine)
docker-compose up -d

# Verify services are running
docker-compose ps
```

Expected output should show all services as "healthy":
```
NAME                    STATUS              PORTS
simulation-engine       Up (healthy)        0.0.0.0:8016->8016/tcp
neo4j                   Up (healthy)        0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
pgvector                Up (healthy)        0.0.0.0:5432->5432/tcp
vllm                    Up                  0.0.0.0:8000->8000/tcp
```

### Option 2: Local Development Setup

For development, you can run the simulation engine directly on your machine.

```bash
# Navigate to the simulation engine directory
cd /home/ranj/Project_Chimera/services/simulation-engine

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env if needed (default values work for local development)
# nano .env  # or use your preferred editor
```

**Environment Variables:**
- `GRAPH_DB_URL` - Neo4j connection URL (default: `bolt://localhost:7687`)
- `GRAPH_DB_USER` - Neo4j username (default: `neo4j`)
- `GRAPH_DB_PASSWORD` - Neo4j password (default: `chimera_graph_2026`)
- `OPENAI_API_KEY` - Optional, for OpenAI LLM capabilities
- `ANTHROPIC_API_KEY` - Optional, for Anthropic Claude LLM capabilities
- `LOCAL_LLM_URL` - Local LLM endpoint (default: `http://localhost:8000`)

```bash
# Start the server
python main.py
```

The server will start on `http://localhost:8016`

## Verification

Verify that the simulation engine is running correctly:

```bash
# Check liveness (is the service running?)
curl http://localhost:8016/health/live
# Expected: {"status":"healthy"}

# Check readiness (are dependencies connected?)
curl http://localhost:8016/health/ready
# Expected: {"status":"ready"}

# View API documentation
open http://localhost:8016/docs  # On macOS
# Or visit http://localhost:8016/docs in your browser
```

## Your First Simulation

Now let's run your first simulation to see the engine in action.

### Step 1: Generate Agent Personas

First, create a diverse population of agents with unique personalities.

```bash
curl -X POST http://localhost:8016/api/v1/agents/generate \
  -H "Content-Type: application/json" \
  -d '{
    "count": 10,
    "seed": 42
  }'
```

**Expected Response:**
```json
{
  "agents": [
    {
      "id": "agent_001",
      "mbti": "INTJ",
      "demographics": {
        "age": 35,
        "education": "graduate",
        "occupation": "data_scientist"
      },
      "behavioral": {
        "openness": 0.8,
        "conscientiousness": 0.7,
        "extraversion": 0.3,
        "agreeableness": 0.5,
        "neuroticism": 0.4
      },
      "political_leaning": "moderate",
      "information_sources": ["academic_journals", "news_analysis"]
    }
    // ... more agents
  ],
  "total": 10
}
```

### Step 2: Run a Simulation

Start a simulation with a scenario. Let's test a policy analysis scenario.

```bash
curl -X POST http://localhost:8016/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 10,
    "simulation_rounds": 5,
    "scenario_description": "A city introduces a congestion pricing policy of $15 per day for downtown driving during peak hours. How will this affect commuter behavior, local businesses, and environmental quality over 6 months?",
    "scenario_type": "policy_analysis",
    "generate_report": true
  }'
```

**Expected Response:**
```json
{
  "simulation_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "message": "Simulation started successfully"
}
```

Save the `simulation_id` from the response - you'll need it to check results.

### Step 3: Check Simulation Status

Monitor your simulation's progress:

```bash
# Replace with your actual simulation ID
SIMULATION_ID="550e8400-e29b-41d4-a716-446655440000"
curl http://localhost:8016/api/v1/simulation/${SIMULATION_ID}/status
```

**Response while running:**
```json
{
  "simulation_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "rounds_completed": 2,
  "total_rounds": 5
}
```

**Response when complete:**
```json
{
  "simulation_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "rounds_completed": 5,
  "total_rounds": 5
}
```

### Step 4: Get Simulation Results

Once complete, retrieve the full results:

```bash
SIMULATION_ID="550e8400-e29b-41d4-a716-446655440000"
curl http://localhost:8016/api/v1/simulation/${SIMULATION_ID}/result | jq
```

**Expected Response:**
```json
{
  "simulation_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "rounds_completed": 5,
  "total_actions": 50,
  "final_summary": "Simulation complete. Agents demonstrated diverse responses to congestion pricing. Key findings: 70% of commuters shifted to public transit, local retail businesses reported initial 15% revenue decline followed by recovery, environmental quality indicators improved by 25%. Confidence: High (0.82).",
  "action_log": [
    [
      {
        "agent_id": "agent_001",
        "action": "analyze_policy",
        "content": "Evaluating congestion pricing impact on daily commute..."
      }
    ]
    // ... more actions
  ]
}
```

## Next Steps

Congratulations! You've successfully run your first simulation. Here's what to explore next:

### Learn More

- **[Running Simulations Guide](running-simulations.md)** - Advanced simulation configuration and best practices
- **[Architecture Overview](../architecture/system-design.md)** - Understand the five-stage pipeline
- **[API Reference](../api/endpoints.md)** - Complete API documentation with all endpoints
- **[Component Reference](../architecture/components.md)** - Deep dive into individual components

### Try These Scenarios

**Social Dynamics:**
```bash
curl -X POST http://localhost:8016/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 50,
    "simulation_rounds": 10,
    "scenario_description": "A new social media platform gains popularity. How does information spread and how does it influence political opinions among users with different starting viewpoints?",
    "scenario_type": "social_dynamics"
  }'
```

**Organizational Behavior:**
```bash
curl -X POST http://localhost:8016/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 25,
    "simulation_rounds": 15,
    "scenario_description": "A company announces a permanent remote work policy. How does this affect team collaboration, employee satisfaction, and productivity over 3 months?",
    "scenario_type": "organizational"
  }'
```

### Advanced Features

- **Agent Interviews** - Query individual agents post-simulation to understand their reasoning
- **Knowledge Graphs** - Build custom knowledge graphs from your documents
- **Report Generation** - Generate comprehensive reports with confidence intervals
- **Metrics** - Monitor token usage and costs via `/metrics` endpoint

## Troubleshooting

### Port Already in Use

If you see "Address already in use" errors:

```bash
# Find process using port 8016
lsof -i :8016

# Kill the process (replace <PID> with actual process ID)
kill -9 <PID>

# Or change the port in .env:
# PORT=8017
```

### Neo4j Connection Failed

If the engine can't connect to Neo4j:

```bash
# Check Neo4j is running (Docker)
docker ps | grep neo4j

# Check Neo4j logs
docker logs neo4j

# If using local Neo4j, start it:
neo4j start

# Or run without Neo4j (limited mode):
# The engine will run but skip graph-based features
```

### Docker Compose Issues

If Docker Compose fails to start services:

```bash
# Stop all services
docker-compose down

# Remove volumes (deletes data)
docker-compose down -v

# Rebuild from scratch
docker-compose up -d --build

# Check logs
docker-compose logs -f simulation-engine
```

### Python Module Import Errors

If you see import errors when running locally:

```bash
# Ensure you're in the simulation-engine directory
cd /home/ranj/Project_Chimera/services/simulation-engine

# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; import neo4j; print('Dependencies OK')"
```

### LLM API Errors

If you see LLM-related errors:

```bash
# The engine uses tiered routing and will work with just local LLMs
# For better results, add API keys to .env:

# OpenAI (optional)
OPENAI_API_KEY=sk-your-key-here

# Anthropic (optional)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Check local LLM is accessible
curl http://localhost:8000/v1/models
```

### Slow Simulation Performance

If simulations are running slowly:

```bash
# Reduce agent count and rounds for testing
{
  "agent_count": 5,
  "simulation_rounds": 3
}

# Check CPU usage
docker stats

# Enable tiered routing (default: 95% local LLM)
# In .env:
ENABLE_TIERED_ROUTING=true
LOCAL_LLM_RATIO=0.95
```

### Getting Help

If you encounter issues not covered here:

1. **Check the logs** - `docker-compose logs -f simulation-engine`
2. **Review configuration** - Verify `.env` settings match your setup
3. **Check API docs** - Visit `http://localhost:8016/docs` for interactive API documentation
4. **Run health checks** - Ensure all services report healthy status
5. **See architecture docs** - Understanding the system helps troubleshooting

## Performance Tips

- **Start small** - Use 5-10 agents and 3-5 rounds for initial testing
- **Use Docker Compose** - Simplifies dependency management
- **Monitor metrics** - Check `/metrics` endpoint for token usage and costs
- **Enable tiered routing** - 95% local LLM usage dramatically reduces costs
- **Cache results** - Save simulation IDs to avoid re-running expensive simulations

## Summary

You've successfully:
- Installed the Chimera Simulation Engine
- Verified all services are running
- Generated agent personas
- Run your first simulation
- Retrieved and analyzed results

The simulation engine is now ready for your "what-if" scenario testing. Experiment with different scenarios, agent counts, and configurations to explore complex social, political, and organizational dynamics.

**Ready to dive deeper?** Check out the [Running Simulations Guide](running-simulations.md) for advanced configuration and best practices.
