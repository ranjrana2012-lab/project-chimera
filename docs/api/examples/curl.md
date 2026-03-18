# curl API Examples

This page provides practical curl examples for interacting with the Chimera Simulation Engine API.

## Prerequisites

Ensure you have curl installed:

```bash
# Check curl version
curl --version

# Install if needed (Ubuntu/Debian)
sudo apt-get install curl

# Install if needed (macOS)
brew install curl
```

Optional: Install jq for JSON pretty-printing:

```bash
# Install jq
sudo apt-get install jq  # Ubuntu/Debian
brew install jq          # macOS
```

## Base URL

All examples use the local development server:

```bash
export CHIMERA_BASE_URL="http://localhost:8016"
```

For production:

```bash
export CHIMERA_BASE_URL="http://simulation-engine:8016"
```

## Health Check Examples

### Basic Health Check

```bash
curl -X GET "${CHIMERA_BASE_URL}/health/live"
```

**Response:**

```json
{
  "status": "healthy",
  "service": "simulation-engine",
  "version": "0.1.0"
}
```

### Health Check with Pretty Output

```bash
curl -X GET "${CHIMERA_BASE_URL}/health/live" | jq '.'
```

### Readiness Check

```bash
curl -X GET "${CHIMERA_BASE_URL}/health/ready" | jq '.'
```

### Verbose Health Check

```bash
curl -v -X GET "${CHIMERA_BASE_URL}/health/live"
```

## Agent Generation Examples

### Generate 10 Default Agents

```bash
curl -X POST "${CHIMERA_BASE_URL}/api/v1/agents/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 10
  }' | jq '.'
```

### Generate Agents with Seed

```bash
curl -X POST "${CHIMERA_BASE_URL}/api/v1/agents/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 25,
    "seed": 42
  }' | jq '.'
```

### Generate Large Batch of Agents

```bash
curl -X POST "${CHIMERA_BASE_URL}/api/v1/agents/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 100,
    "seed": 12345
  }' | jq '{
    count: .count,
    first_three: .personas[:3]
  }'
```

### Save Generated Agents to File

```bash
curl -X POST "${CHIMERA_BASE_URL}/api/v1/agents/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 50,
    "seed": 999
  }' | jq '.' > agents.json

# View first agent
cat agents.json | jq '.personas[0]'
```

## Simulation Examples

### Basic Simulation

```bash
curl -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 25,
    "simulation_rounds": 15,
    "scenario_description": "Debate the ethics of autonomous vehicles in urban environments"
  }' | jq '.'
```

### Simulation with Topic and Report

```bash
curl -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 30,
    "simulation_rounds": 20,
    "scenario_description": "Discuss the implications of implementing AI-driven diagnostic tools in public healthcare systems",
    "scenario_topic": "AI in Healthcare Policy",
    "generate_report": true
  }' | jq '.'
```

### Simulation with Seed Documents

```bash
curl -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 40,
    "simulation_rounds": 15,
    "scenario_description": "Develop a comprehensive climate action plan for a mid-sized city",
    "scenario_topic": "Climate Policy Planning",
    "seed_documents": [
      "Climate change is causing rising sea levels and extreme weather events globally.",
      "Renewable energy sources like solar and wind are becoming cost-competitive with fossil fuels.",
      "Carbon capture technologies can reduce greenhouse gas emissions from industrial processes."
    ],
    "generate_report": false
  }' | jq '.'
```

### Minimal Simulation (Fastest)

```bash
curl -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 10,
    "simulation_rounds": 5,
    "scenario_description": "Quick test simulation"
  }' | jq '.'
```

### Large-Scale Simulation

```bash
curl -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 100,
    "simulation_rounds": 25,
    "scenario_description": "Evaluate the impact of universal basic income on workforce participation and economic mobility",
    "scenario_topic": "Economic Policy",
    "generate_report": true
  }' | jq '.'
```

## Knowledge Graph Examples

### Build Basic Knowledge Graph

```bash
curl -X POST "${CHIMERA_BASE_URL}/api/v1/graph/build" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      "The immune system protects the body from infection.",
      "White blood cells are a key component of immune response."
    ]
  }' | jq '.'
```

### Build Graph from Multiple Documents

```bash
curl -X POST "${CHIMERA_BASE_URL}/api/v1/graph/build" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      "Climate change is causing rising sea levels and extreme weather events globally.",
      "Renewable energy sources like solar and wind are becoming cost-competitive with fossil fuels.",
      "Carbon capture technologies can reduce greenhouse gas emissions from industrial processes.",
      "Urban planning strategies include green infrastructure and public transportation improvements.",
      "International cooperation is essential for addressing global climate challenges effectively."
    ]
  }' | jq '.'
```

## Real-World Scenarios

### Scenario 1: Healthcare Policy Discussion

```bash
#!/bin/bash

# Generate diverse stakeholders
echo "Generating healthcare stakeholders..."
curl -X POST "${CHIMERA_BASE_URL}/api/v1/agents/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 50,
    "seed": 456
  }' | jq '.count' > /dev/null

# Run healthcare policy simulation
echo "Running healthcare policy simulation..."
curl -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 50,
    "simulation_rounds": 20,
    "scenario_description": "Discuss the implications and challenges of implementing AI-driven diagnostic tools in public healthcare systems, considering patient safety, cost-effectiveness, and ethical considerations",
    "scenario_topic": "AI in Healthcare Policy",
    "seed_documents": [
      "AI has the potential to revolutionize medical diagnosis by analyzing imaging data with high accuracy.",
      "Machine learning algorithms can predict patient outcomes and recommend personalized treatment plans.",
      "Telemedicine platforms enabled by AI can provide healthcare access to rural and underserved communities.",
      "Concerns about data privacy and algorithmic bias must be addressed in AI healthcare implementations."
    ],
    "generate_report": true
  }' | jq '{
    simulation_id: .simulation_id,
    status: .status,
    rounds_completed: .rounds_completed,
    total_actions: .total_actions
  }'
```

### Scenario 2: Urban Planning Workshop

```bash
#!/bin/bash

echo "Running urban planning simulation..."

curl -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 35,
    "simulation_rounds": 15,
    "scenario_description": "Design a sustainable urban transportation system for 2030 that balances accessibility, environmental impact, and economic viability",
    "scenario_topic": "Urban Transportation Planning",
    "seed_documents": [
      "Electric public transit reduces carbon emissions and operating costs over time.",
      "Integrated bike-sharing networks complement public transportation systems.",
      "Smart traffic management can reduce congestion by 30% in dense urban areas.",
      "Pedestrian-friendly urban design improves public health and local commerce."
    ],
    "generate_report": false
  }' | jq '{
    simulation_id: .simulation_id,
    summary: .summary
  }'
```

### Scenario 3: Education Reform Discussion

```bash
#!/bin/bash

echo "Running education reform simulation..."

curl -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 40,
    "simulation_rounds": 18,
    "scenario_description": "Propose comprehensive reforms to improve STEM education accessibility and outcomes in underserved communities",
    "scenario_topic": "Education Reform",
    "seed_documents": [
      "Project-based learning improves student engagement and retention in STEM subjects.",
      "Virtual laboratories provide hands-on experience without expensive equipment.",
      "Teacher training in digital literacy is crucial for modern education success.",
      "Community partnerships can bridge resource gaps in underfunded schools."
    ],
    "generate_report": true
  }' | jq '{
    simulation_id: .simulation_id,
    rounds_completed: .rounds_completed,
    total_actions: .total_actions
  }'
```

## Advanced Usage

### Time a Simulation

```bash
time curl -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 25,
    "simulation_rounds": 10,
    "scenario_description": "Test simulation for timing"
  }' | jq '.simulation_id'
```

### Save Simulation Result

```bash
curl -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 30,
    "simulation_rounds": 15,
    "scenario_description": "Remote work policy development",
    "scenario_topic": "Remote Work Policy"
  }' | jq '.' > simulation_result.json

# Extract key information
cat simulation_result.json | jq '{
  id: .simulation_id,
  status: .status,
  rounds: .rounds_completed,
  actions: .total_actions
  }'
```

### Batch Simulations

```bash
#!/bin/bash

# Run multiple scenarios for comparison
scenarios=(
  "Urban Transportation:Design a sustainable urban transportation system for 2030"
  "Education Reform:Propose reforms to improve STEM education accessibility"
  "Remote Work:Address challenges and opportunities of permanent remote work policies"
)

for scenario in "${scenarios[@]}"; do
  IFS=':' read -r topic description <<< "$scenario"

  echo "Running scenario: $topic"

  curl -s -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
    -H "Content-Type: application/json" \
    -d "{
      \"agent_count\": 20,
      \"simulation_rounds\": 10,
      \"scenario_description\": \"$description\",
      \"scenario_topic\": \"$topic\"
    }" | jq "{
      topic: \"$topic\",
      simulation_id: .simulation_id,
      total_actions: .total_actions
    }"

  echo ""
done
```

### Error Handling Example

```bash
#!/bin/bash

# Check health first
health_status=$(curl -s -X GET "${CHIMERA_BASE_URL}/health/live" | jq -r '.status')

if [ "$health_status" != "healthy" ]; then
  echo "Error: Service is not healthy (status: $health_status)"
  exit 1
fi

echo "Service is healthy, starting simulation..."

# Run simulation with error handling
response=$(curl -s -w "\n%{http_code}" -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 25,
    "simulation_rounds": 15,
    "scenario_description": "Test simulation"
  }')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" != "200" ]; then
  echo "Error: HTTP $http_code"
  echo "$body" | jq '.'
  exit 1
fi

echo "Simulation successful:"
echo "$body" | jq '.'
```

### Progress Monitoring (for long simulations)

```bash
#!/bin/bash

echo "Starting long simulation..."

# Start simulation in background
curl -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 100,
    "simulation_rounds": 25,
    "scenario_description": "Comprehensive policy analysis",
    "generate_report": true
  }' > simulation_output.json 2>&1 &

curl_pid=$!

echo "Simulation started (PID: $curl_pid)"
echo "Waiting for completion..."

# Wait for curl to finish
wait $curl_pid

echo "Simulation completed!"
cat simulation_output.json | jq '{
  simulation_id: .simulation_id,
  status: .status,
  rounds_completed: .rounds_completed,
  total_actions: .total_actions
}'
```

## Testing and Debugging

### Verbose Mode for Debugging

```bash
curl -v -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 5,
    "simulation_rounds": 3,
    "scenario_description": "Debug test"
  }'
```

### Test Response Headers

```bash
curl -i -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 5,
    "simulation_rounds": 3,
    "scenario_description": "Header test"
  }'
```

### Measure Response Time

```bash
curl -w "\nTotal time: %{time_total}s\n" \
  -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 10,
    "simulation_rounds": 5,
    "scenario_description": "Performance test"
  }' -o /dev/null -s
```

## Tips and Best Practices

1. **Use jq for JSON parsing** - Makes responses much more readable
2. **Check health first** - Verify service availability before running simulations
3. **Use appropriate timeouts** - Add `--max-time` for long-running requests
4. **Save results to files** - Useful for later analysis and comparison
5. **Start small** - Test with small simulations before scaling up
6. **Use scripts for automation** - Save complex workflows as reusable shell scripts

## Common Issues and Solutions

### Connection Refused

```bash
# Check if service is running
curl -v "${CHIMERA_BASE_URL}/health/live"

# If connection refused, start the service:
# cd /path/to/chimera
# docker-compose up simulation-engine
```

### Timeout Errors

```bash
# Increase timeout for large simulations
curl --max-time 300 -X POST "${CHIMERA_BASE_URL}/api/v1/simulation/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 100,
    "simulation_rounds": 25,
    "scenario_description": "Large simulation"
  }'
```

### JSON Validation Errors

```bash
# Validate JSON before sending
echo '{
  "agent_count": 25,
  "simulation_rounds": 15
}' | jq '.'

# Then use in curl
```

## Related Documentation

- [API Endpoints Reference](../endpoints.md)
- [Data Models](../models.md)
- [Python Examples](./python.md)
- [JavaScript Examples](./javascript.md)
