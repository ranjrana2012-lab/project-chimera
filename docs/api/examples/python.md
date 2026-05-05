# Python API Examples

This page provides practical Python examples for interacting with the Chimera Simulation Engine API.

## Prerequisites

Install the required dependencies:

```bash
pip install httpx
```

Or install with asyncio support:

```bash
pip install httpx[http2]
```

## Basic Setup

```python
import asyncio
import httpx
from typing import Optional, Dict, Any

class ChimeraClient:
    """Async client for Chimera Simulation Engine API."""

    def __init__(self, base_url: str = "http://localhost:8016"):
        self.base_url = base_url
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """Check if the service is healthy."""
        if not self.client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        response = await self.client.get("/health/live")
        response.raise_for_status()
        return response.json()

    async def generate_agents(self, count: int = 10, seed: Optional[int] = None) -> Dict[str, Any]:
        """Generate agent personas."""
        payload = {"count": count}
        if seed is not None:
            payload["seed"] = seed

        response = await self.client.post("/api/v1/agents/generate", json=payload)
        response.raise_for_status()
        return response.json()

    async def start_simulation(
        self,
        agent_count: int,
        simulation_rounds: int,
        scenario_description: str,
        scenario_topic: Optional[str] = None,
        seed_documents: Optional[list] = None,
        generate_report: bool = False
    ) -> Dict[str, Any]:
        """Start a new simulation."""
        payload = {
            "agent_count": agent_count,
            "simulation_rounds": simulation_rounds,
            "scenario_description": scenario_description,
            "generate_report": generate_report
        }

        if scenario_topic:
            payload["scenario_topic"] = scenario_topic
        if seed_documents:
            payload["seed_documents"] = seed_documents

        response = await self.client.post("/api/v1/simulation/simulate", json=payload)
        response.raise_for_status()
        return response.json()

    async def build_graph(self, documents: list) -> Dict[str, Any]:
        """Build a knowledge graph from documents."""
        payload = {"documents": documents}

        response = await self.client.post("/api/v1/graph/build", json=payload)
        response.raise_for_status()
        return response.json()
```

## Example 1: Basic Simulation Workflow

```python
import asyncio
from chimera_client import ChimeraClient

async def basic_simulation_example():
    """Run a basic simulation with generated agents."""

    async with ChimeraClient() as client:
        # Check service health
        print("Checking service health...")
        health = await client.health_check()
        print(f"Service status: {health['status']}")

        # Generate agents
        print("\nGenerating agents...")
        agents = await client.generate_agents(count=25, seed=42)
        print(f"Generated {agents['count']} agents")

        # Start a simulation
        print("\nStarting simulation...")
        result = await client.start_simulation(
            agent_count=25,
            simulation_rounds=15,
            scenario_description="Debate the ethics of autonomous vehicles in urban environments",
            scenario_topic="Ethics of AI",
            generate_report=True
        )

        print(f"\nSimulation completed!")
        print(f"Simulation ID: {result['simulation_id']}")
        print(f"Status: {result['status']}")
        print(f"Rounds completed: {result['rounds_completed']}")
        print(f"Total actions: {result['total_actions']}")
        print(f"Summary: {result['summary'][:100]}...")

if __name__ == "__main__":
    asyncio.run(basic_simulation_example())
```

## Example 2: Healthcare Policy Discussion

```python
import asyncio
from chimera_client import ChimeraClient

async def healthcare_simulation():
    """Simulate a healthcare policy discussion with diverse perspectives."""

    async with ChimeraClient() as client:
        # Prepare seed documents for context
        seed_docs = [
            "AI has the potential to revolutionize medical diagnosis by analyzing imaging data with high accuracy.",
            "Machine learning algorithms can predict patient outcomes and recommend personalized treatment plans.",
            "Telemedicine platforms enabled by AI can provide healthcare access to rural and underserved communities.",
            "Concerns about data privacy and algorithmic bias must be addressed in AI healthcare implementations."
        ]

        # Generate diverse agent personas
        print("Generating healthcare professionals and stakeholders...")
        agents = await client.generate_agents(count=50, seed=123)
        print(f"Generated {agents['count']} diverse stakeholders")

        # Run simulation with healthcare focus
        print("\nRunning healthcare policy simulation...")
        result = await client.start_simulation(
            agent_count=50,
            simulation_rounds=20,
            scenario_description="Discuss the implications and challenges of implementing AI-driven diagnostic tools in public healthcare systems, considering patient safety, cost-effectiveness, and ethical considerations",
            scenario_topic="AI in Healthcare Policy",
            seed_documents=seed_docs,
            generate_report=True
        )

        print(f"\nSimulation Results:")
        print(f"ID: {result['simulation_id']}")
        print(f"Status: {result['status']}")
        print(f"Rounds: {result['rounds_completed']}/{result.get('rounds_requested', 'N/A')}")
        print(f"Actions: {result['total_actions']}")
        print(f"\nSummary:\n{result['summary']}")

if __name__ == "__main__":
    asyncio.run(healthcare_simulation())
```

## Example 3: Knowledge Graph Integration

```python
import asyncio
from chimera_client import ChimeraClient

async def graph_based_simulation():
    """Build a knowledge graph and use it for simulation context."""

    async with ChimeraClient() as client:
        # Build knowledge graph from research documents
        print("Building knowledge graph...")
        documents = [
            "Climate change is causing rising sea levels and extreme weather events globally.",
            "Renewable energy sources like solar and wind are becoming cost-competitive with fossil fuels.",
            "Carbon capture technologies can reduce greenhouse gas emissions from industrial processes.",
            "Urban planning strategies include green infrastructure and public transportation improvements.",
            "International cooperation is essential for addressing global climate challenges effectively."
        ]

        graph = await client.build_graph(documents)
        print(f"Graph built: {graph['entities']} entities, {graph['relationships']} relationships")
        print(f"Graph ID: {graph['graph_id']}")

        # Run simulation using graph-derived context
        print("\nRunning climate policy simulation...")
        result = await client.start_simulation(
            agent_count=30,
            simulation_rounds=15,
            scenario_description="Develop a comprehensive climate action plan for a mid-sized city, balancing economic growth, environmental protection, and social equity",
            scenario_topic="Climate Policy Planning",
            seed_documents=documents,
            generate_report=False
        )

        print(f"\nSimulation completed: {result['simulation_id']}")
        print(f"Summary: {result['summary'][:200]}...")

if __name__ == "__main__":
    asyncio.run(graph_based_simulation())
```

## Example 4: Multiple Concurrent Simulations

```python
import asyncio
from chimera_client import ChimeraClient
from typing import List

async def run_multiple_simulations():
    """Run multiple simulations concurrently for comparison."""

    scenarios = [
        {
            "topic": "Urban Transportation",
            "description": "Design a sustainable urban transportation system for 2030"
        },
        {
            "topic": "Education Reform",
            "description": "Propose reforms to improve STEM education accessibility"
        },
        {
            "topic": "Remote Work",
            "description": "Address challenges and opportunities of permanent remote work policies"
        }
    ]

    async def run_scenario(scenario: dict) -> dict:
        """Run a single scenario."""
        async with ChimeraClient() as client:
            result = await client.start_simulation(
                agent_count=20,
                simulation_rounds=10,
                scenario_description=scenario["description"],
                scenario_topic=scenario["topic"],
                generate_report=False
            )
            return {
                "topic": scenario["topic"],
                "simulation_id": result["simulation_id"],
                "total_actions": result["total_actions"],
                "summary": result["summary"][:150]
            }

    # Run all scenarios concurrently
    print("Running concurrent simulations...")
    results = await asyncio.gather(*[run_scenario(s) for s in scenarios])

    # Display results
    print("\n=== Simulation Results ===")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Topic: {result['topic']}")
        print(f"   Simulation ID: {result['simulation_id']}")
        print(f"   Total Actions: {result['total_actions']}")
        print(f"   Summary: {result['summary']}...")

if __name__ == "__main__":
    asyncio.run(run_multiple_simulations())
```

## Example 5: Error Handling and Retry Logic

```python
import asyncio
import logging
from httpx import HTTPStatusError, TimeoutException
from chimera_client import ChimeraClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def resilient_simulation():
    """Run a simulation with robust error handling and retries."""

    max_retries = 3
    retry_delay = 2  # seconds

    async with ChimeraClient() as client:
        # Check health with retries
        for attempt in range(max_retries):
            try:
                health = await client.health_check()
                logger.info(f"Service is healthy: {health['status']}")
                break
            except (HTTPStatusError, TimeoutException) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Health check failed (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Service unavailable after {max_retries} attempts")
                    return

        # Run simulation with error handling
        try:
            result = await client.start_simulation(
                agent_count=25,
                simulation_rounds=15,
                scenario_description="Evaluate the impact of universal basic income on workforce participation",
                scenario_topic="Economic Policy",
                generate_report=True
            )

            logger.info(f"Simulation successful: {result['simulation_id']}")
            logger.info(f"Status: {result['status']}")
            logger.info(f"Summary: {result['summary'][:200]}...")

        except HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
        except TimeoutException:
            logger.error("Request timed out. The simulation may be taking longer than expected.")
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(resilient_simulation())
```

## Example 6: Batch Agent Generation

```python
import asyncio
from chimera_client import ChimeraClient

async def batch_agent_generation():
    """Generate agents in batches for large-scale simulations."""

    batch_size = 100
    total_agents = 500
    batches = (total_agents + batch_size - 1) // batch_size

    async with ChimeraClient() as client:
        print(f"Generating {total_agents} agents in {batches} batches of {batch_size}...")

        all_agents = []
        for i in range(batches):
            batch_num = i + 1
            seed = 1000 + batch_num  # Unique seed for each batch

            result = await client.generate_agents(
                count=batch_size,
                seed=seed
            )

            all_agents.extend(result["personas"])
            print(f"Batch {batch_num}/{batches}: Generated {len(result['personas'])} agents")

        print(f"\nTotal agents generated: {len(all_agents)}")

        # Display sample agents
        print("\nSample agents:")
        for agent in all_agents[:3]:
            print(f"\n  Name: {agent['name']}")
            print(f"  Occupation: {agent['occupation']}")
            print(f"  Traits: {', '.join(agent['personality_traits'])}")

if __name__ == "__main__":
    asyncio.run(batch_agent_generation())
```

## Tips and Best Practices

1. **Always use async context managers** to ensure proper resource cleanup
2. **Set appropriate timeouts** based on your simulation complexity
3. **Implement error handling** for network issues and service errors
4. **Use unique seeds** for reproducible agent generation
5. **Monitor simulation metrics** to track performance and costs
6. **Start with smaller simulations** for testing before scaling up

## Related Documentation

- [API Endpoints Reference](../endpoints.md)
- [Data Models](../models.md)
- [Student / Laptop Setup](../../guides/STUDENT_LAPTOP_SETUP.md)
