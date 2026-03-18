# JavaScript API Examples

This page provides practical JavaScript examples for interacting with the Chimera Simulation Engine API using the fetch API.

## Prerequisites

Modern JavaScript environments include the fetch API natively:

- **Node.js 18+**: Built-in fetch support
- **Modern browsers**: Native fetch support
- **Node.js 16-**: Install `node-fetch`

For older Node.js versions:

```bash
npm install node-fetch
```

## Basic Setup

### ES6 Modules (Recommended)

```javascript
// chimera-client.js
class ChimeraClient {
  constructor(baseUrl = 'http://localhost:8016') {
    this.baseUrl = baseUrl;
  }

  async #request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: response.statusText,
      }));
      throw new Error(`HTTP ${response.status}: ${error.detail}`);
    }

    return response.json();
  }

  async healthCheck() {
    return this.#request('/health/live');
  }

  async readinessCheck() {
    return this.#request('/health/ready');
  }

  async generateAgents(count, seed = null) {
    const payload = { count };
    if (seed !== null) {
      payload.seed = seed;
    }
    return this.#request('/api/v1/agents/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async startSimulation(options) {
    const {
      agentCount,
      simulationRounds,
      scenarioDescription,
      scenarioTopic = null,
      seedDocuments = null,
      generateReport = false,
    } = options;

    const payload = {
      agent_count: agentCount,
      simulation_rounds: simulationRounds,
      scenario_description: scenarioDescription,
      generate_report: generateReport,
    };

    if (scenarioTopic) {
      payload.scenario_topic = scenarioTopic;
    }
    if (seedDocuments) {
      payload.seed_documents = seedDocuments;
    }

    return this.#request('/api/v1/simulation/simulate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async buildGraph(documents) {
    return this.#request('/api/v1/graph/build', {
      method: 'POST',
      body: JSON.stringify({ documents }),
    });
  }
}

export default ChimeraClient;
```

### CommonJS (Node.js)

```javascript
// chimera-client.cjs
class ChimeraClient {
  constructor(baseUrl = 'http://localhost:8016') {
    this.baseUrl = baseUrl;
  }

  async #request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: response.statusText,
      }));
      throw new Error(`HTTP ${response.status}: ${error.detail}`);
    }

    return response.json();
  }

  // ... (same methods as ES6 version)

  async healthCheck() {
    return this.#request('/health/live');
  }

  async generateAgents(count, seed = null) {
    const payload = { count };
    if (seed !== null) {
      payload.seed = seed;
    }
    return this.#request('/api/v1/agents/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async startSimulation(options) {
    const {
      agentCount,
      simulationRounds,
      scenarioDescription,
      scenarioTopic = null,
      seedDocuments = null,
      generateReport = false,
    } = options;

    const payload = {
      agent_count: agentCount,
      simulation_rounds: simulationRounds,
      scenario_description: scenarioDescription,
      generate_report: generateReport,
    };

    if (scenarioTopic) {
      payload.scenario_topic = scenarioTopic;
    }
    if (seedDocuments) {
      payload.seed_documents = seedDocuments;
    }

    return this.#request('/api/v1/simulation/simulate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }
}

module.exports = ChimeraClient;
```

## Example 1: Basic Simulation Workflow

```javascript
// examples/basic-simulation.js
import ChimeraClient from './chimera-client.js';

async function basicSimulation() {
  const client = new ChimeraClient();

  try {
    // Check service health
    console.log('Checking service health...');
    const health = await client.healthCheck();
    console.log(`Service status: ${health.status}`);

    // Generate agents
    console.log('\nGenerating agents...');
    const agents = await client.generateAgents(25, 42);
    console.log(`Generated ${agents.count} agents`);

    // Start simulation
    console.log('\nStarting simulation...');
    const result = await client.startSimulation({
      agentCount: 25,
      simulationRounds: 15,
      scenarioDescription: 'Debate the ethics of autonomous vehicles in urban environments',
      scenarioTopic: 'Ethics of AI',
      generateReport: true,
    });

    console.log('\nSimulation completed!');
    console.log(`Simulation ID: ${result.simulation_id}`);
    console.log(`Status: ${result.status}`);
    console.log(`Rounds completed: ${result.rounds_completed}`);
    console.log(`Total actions: ${result.total_actions}`);
    console.log(`Summary: ${result.summary.substring(0, 100)}...`);

  } catch (error) {
    console.error('Error:', error.message);
  }
}

basicSimulation();
```

## Example 2: Healthcare Policy Discussion

```javascript
// examples/healthcare-simulation.js
import ChimeraClient from './chimera-client.js';

async function healthcareSimulation() {
  const client = new ChimeraClient();

  try {
    // Prepare seed documents
    const seedDocs = [
      'AI has the potential to revolutionize medical diagnosis by analyzing imaging data with high accuracy.',
      'Machine learning algorithms can predict patient outcomes and recommend personalized treatment plans.',
      'Telemedicine platforms enabled by AI can provide healthcare access to rural and underserved communities.',
      'Concerns about data privacy and algorithmic bias must be addressed in AI healthcare implementations.',
    ];

    // Generate diverse stakeholders
    console.log('Generating healthcare professionals and stakeholders...');
    const agents = await client.generateAgents(50, 123);
    console.log(`Generated ${agents.count} diverse stakeholders`);

    // Run simulation
    console.log('\nRunning healthcare policy simulation...');
    const result = await client.startSimulation({
      agentCount: 50,
      simulationRounds: 20,
      scenarioDescription: 'Discuss the implications and challenges of implementing AI-driven diagnostic tools in public healthcare systems, considering patient safety, cost-effectiveness, and ethical considerations',
      scenarioTopic: 'AI in Healthcare Policy',
      seedDocuments: seedDocs,
      generateReport: true,
    });

    console.log('\nSimulation Results:');
    console.log(`ID: ${result.simulation_id}`);
    console.log(`Status: ${result.status}`);
    console.log(`Rounds: ${result.rounds_completed}`);
    console.log(`Actions: ${result.total_actions}`);
    console.log(`\nSummary:\n${result.summary}`);

  } catch (error) {
    console.error('Error:', error.message);
  }
}

healthcareSimulation();
```

## Example 3: Knowledge Graph Integration

```javascript
// examples/graph-simulation.js
import ChimeraClient from './chimera-client.js';

async function graphBasedSimulation() {
  const client = new ChimeraClient();

  try {
    // Build knowledge graph
    console.log('Building knowledge graph...');
    const documents = [
      'Climate change is causing rising sea levels and extreme weather events globally.',
      'Renewable energy sources like solar and wind are becoming cost-competitive with fossil fuels.',
      'Carbon capture technologies can reduce greenhouse gas emissions from industrial processes.',
      'Urban planning strategies include green infrastructure and public transportation improvements.',
      'International cooperation is essential for addressing global climate challenges effectively.',
    ];

    const graph = await client.buildGraph(documents);
    console.log(`Graph built: ${graph.entities} entities, ${graph.relationships} relationships`);
    console.log(`Graph ID: ${graph.graph_id}`);

    // Run simulation
    console.log('\nRunning climate policy simulation...');
    const result = await client.startSimulation({
      agentCount: 30,
      simulationRounds: 15,
      scenarioDescription: 'Develop a comprehensive climate action plan for a mid-sized city, balancing economic growth, environmental protection, and social equity',
      scenarioTopic: 'Climate Policy Planning',
      seedDocuments: documents,
      generateReport: false,
    });

    console.log(`\nSimulation completed: ${result.simulation_id}`);
    console.log(`Summary: ${result.summary.substring(0, 200)}...`);

  } catch (error) {
    console.error('Error:', error.message);
  }
}

graphBasedSimulation();
```

## Example 4: Multiple Concurrent Simulations

```javascript
// examples/concurrent-simulations.js
import ChimeraClient from './chimera-client.js';

const scenarios = [
  {
    topic: 'Urban Transportation',
    description: 'Design a sustainable urban transportation system for 2030',
  },
  {
    topic: 'Education Reform',
    description: 'Propose reforms to improve STEM education accessibility',
  },
  {
    topic: 'Remote Work',
    description: 'Address challenges and opportunities of permanent remote work policies',
  },
];

async function runScenario(scenario) {
  const client = new ChimeraClient();

  try {
    const result = await client.startSimulation({
      agentCount: 20,
      simulationRounds: 10,
      scenarioDescription: scenario.description,
      scenarioTopic: scenario.topic,
      generateReport: false,
    });

    return {
      topic: scenario.topic,
      simulationId: result.simulation_id,
      totalActions: result.total_actions,
      summary: result.summary.substring(0, 150),
    };
  } catch (error) {
    return {
      topic: scenario.topic,
      error: error.message,
    };
  }
}

async function runMultipleSimulations() {
  console.log('Running concurrent simulations...');

  const results = await Promise.all(
    scenarios.map(scenario => runScenario(scenario))
  );

  console.log('\n=== Simulation Results ===');
  results.forEach((result, index) => {
    console.log(`\n${index + 1}. Topic: ${result.topic}`);
    if (result.error) {
      console.log(`   Error: ${result.error}`);
    } else {
      console.log(`   Simulation ID: ${result.simulationId}`);
      console.log(`   Total Actions: ${result.totalActions}`);
      console.log(`   Summary: ${result.summary}...`);
    }
  });
}

runMultipleSimulations();
```

## Example 5: Error Handling and Retry Logic

```javascript
// examples/resilient-simulation.js
import ChimeraClient from './chimera-client.js';

async function waitForHealth(client, maxRetries = 3, retryDelay = 2000) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const health = await client.healthCheck();
      console.log(`Service is healthy: ${health.status}`);
      return true;
    } catch (error) {
      if (attempt < maxRetries) {
        console.warn(`Health check failed (attempt ${attempt}): ${error.message}`);
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      } else {
        console.error(`Service unavailable after ${maxRetries} attempts`);
        return false;
      }
    }
  }
  return false;
}

async function resilientSimulation() {
  const client = new ChimeraClient();

  // Check health with retries
  const isHealthy = await waitForHealth(client);
  if (!isHealthy) {
    return;
  }

  // Run simulation with error handling
  try {
    const result = await client.startSimulation({
      agentCount: 25,
      simulationRounds: 15,
      scenarioDescription: 'Evaluate the impact of universal basic income on workforce participation',
      scenarioTopic: 'Economic Policy',
      generateReport: true,
    });

    console.log(`Simulation successful: ${result.simulation_id}`);
    console.log(`Status: ${result.status}`);
    console.log(`Summary: ${result.summary.substring(0, 200)}...`);

  } catch (error) {
    if (error.message.includes('HTTP 503')) {
      console.error('Service unavailable. Please try again later.');
    } else if (error.message.includes('HTTP 422')) {
      console.error('Invalid request parameters.');
    } else {
      console.error(`Unexpected error: ${error.message}`);
    }
  }
}

resilientSimulation();
```

## Example 6: Browser-Based Interaction

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chimera Simulation Demo</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }
    .form-group {
      margin-bottom: 15px;
    }
    label {
      display: block;
      margin-bottom: 5px;
      font-weight: bold;
    }
    textarea {
      width: 100%;
      height: 100px;
      padding: 8px;
      box-sizing: border-box;
    }
    input[type="number"] {
      width: 100px;
      padding: 8px;
    }
    button {
      background-color: #4CAF50;
      color: white;
      padding: 10px 20px;
      border: none;
      cursor: pointer;
      font-size: 16px;
    }
    button:hover {
      background-color: #45a049;
    }
    button:disabled {
      background-color: #cccccc;
      cursor: not-allowed;
    }
    #result {
      margin-top: 20px;
      padding: 15px;
      background-color: #f0f0f0;
      border-radius: 5px;
      white-space: pre-wrap;
    }
    .error {
      color: red;
    }
  </style>
</head>
<body>
  <h1>Chimera Simulation Demo</h1>

  <form id="simulationForm">
    <div class="form-group">
      <label for="agentCount">Agent Count:</label>
      <input type="number" id="agentCount" min="1" max="100" value="25">
    </div>

    <div class="form-group">
      <label for="rounds">Simulation Rounds:</label>
      <input type="number" id="rounds" min="1" max="50" value="15">
    </div>

    <div class="form-group">
      <label for="topic">Topic:</label>
      <input type="text" id="topic" value="Ethics of AI">
    </div>

    <div class="form-group">
      <label for="description">Scenario Description:</label>
      <textarea id="description" required>Debate the ethics of autonomous vehicles in urban environments</textarea>
    </div>

    <button type="submit" id="submitBtn">Run Simulation</button>
  </form>

  <div id="result"></div>

  <script>
    const API_BASE = 'http://localhost:8016';

    document.getElementById('simulationForm').addEventListener('submit', async (e) => {
      e.preventDefault();

      const submitBtn = document.getElementById('submitBtn');
      const resultDiv = document.getElementById('result');

      submitBtn.disabled = true;
      submitBtn.textContent = 'Running...';
      resultDiv.textContent = 'Starting simulation...';

      try {
        const payload = {
          agent_count: parseInt(document.getElementById('agentCount').value),
          simulation_rounds: parseInt(document.getElementById('rounds').value),
          scenario_description: document.getElementById('description').value,
          scenario_topic: document.getElementById('topic').value,
          generate_report: false,
        };

        const response = await fetch(`${API_BASE}/api/v1/simulation/simulate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || response.statusText);
        }

        const result = await response.json();

        resultDiv.textContent = `
Simulation completed successfully!

Simulation ID: ${result.simulation_id}
Status: ${result.status}
Rounds completed: ${result.rounds_completed}
Total actions: ${result.total_actions}

Summary:
${result.summary}
        `;

      } catch (error) {
        resultDiv.textContent = `Error: ${error.message}`;
        resultDiv.classList.add('error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Run Simulation';
      }
    });
  </script>
</body>
</html>
```

## Example 7: Progress Monitoring

```javascript
// examples/monitored-simulation.js
import ChimeraClient from './chimera-client.js';

async function runMonitoredSimulation() {
  const client = new ChimeraClient();

  const startTime = Date.now();

  console.log('Starting monitored simulation...');

  try {
    const result = await client.startSimulation({
      agentCount: 50,
      simulationRounds: 20,
      scenarioDescription: 'Complex policy analysis with multiple stakeholders',
      scenarioTopic: 'Policy Analysis',
      generateReport: true,
    });

    const duration = Date.now() - startTime;
    const durationSeconds = (duration / 1000).toFixed(2);

    console.log('\n=== Simulation Metrics ===');
    console.log(`Duration: ${durationSeconds}s`);
    console.log(`Simulation ID: ${result.simulation_id}`);
    console.log(`Status: ${result.status}`);
    console.log(`Rounds completed: ${result.rounds_completed}`);
    console.log(`Total actions: ${result.total_actions}`);
    console.log(`Actions per second: ${(result.total_actions / durationSeconds).toFixed(2)}`);

  } catch (error) {
    console.error('Simulation failed:', error.message);
  }
}

runMonitoredSimulation();
```

## Example 8: Batch Processing

```javascript
// examples/batch-simulation.js
import ChimeraClient from './chimera-client.js';

async function runBatchSimulation() {
  const client = new ChimeraClient();

  const scenarios = [
    {
      name: 'Healthcare',
      description: 'AI in healthcare policy discussion',
      agents: 30,
      rounds: 15,
    },
    {
      name: 'Transportation',
      description: 'Urban transportation planning',
      agents: 25,
      rounds: 12,
    },
    {
      name: 'Education',
      description: 'STEM education reform',
      agents: 35,
      rounds: 18,
    },
  ];

  const results = [];

  for (const scenario of scenarios) {
    console.log(`\nRunning ${scenario.name} simulation...`);

    try {
      const start = Date.now();

      const result = await client.startSimulation({
        agentCount: scenario.agents,
        simulationRounds: scenario.rounds,
        scenarioDescription: scenario.description,
        scenarioTopic: scenario.name,
        generateReport: false,
      });

      const duration = ((Date.now() - start) / 1000).toFixed(2);

      results.push({
        scenario: scenario.name,
        success: true,
        simulationId: result.simulation_id,
        duration: `${duration}s`,
        totalActions: result.total_actions,
      });

      console.log(`  Completed in ${duration}s`);
      console.log(`  Actions: ${result.total_actions}`);

    } catch (error) {
      results.push({
        scenario: scenario.name,
        success: false,
        error: error.message,
      });
      console.error(`  Failed: ${error.message}`);
    }
  }

  console.log('\n=== Batch Summary ===');
  results.forEach((result, index) => {
    console.log(`\n${index + 1}. ${result.scenario}`);
    if (result.success) {
      console.log(`   ✓ Success (${result.duration})`);
      console.log(`   Actions: ${result.totalActions}`);
    } else {
      console.log(`   ✗ Failed: ${result.error}`);
    }
  });
}

runBatchSimulation();
```

## Tips and Best Practices

1. **Use async/await** - Makes asynchronous code more readable
2. **Implement error handling** - Always wrap API calls in try-catch
3. **Set timeouts** - Use AbortController for long-running requests
4. **Validate inputs** - Check parameters before making requests
5. **Log important events** - Track simulation IDs and results
6. **Handle concurrent requests** - Use Promise.all() for parallel operations
7. **Use TypeScript** - Add type safety for better development experience

## TypeScript Support

For TypeScript users, here's a typed version:

```typescript
// chimera-client.ts
interface SimulationOptions {
  agentCount: number;
  simulationRounds: number;
  scenarioDescription: string;
  scenarioTopic?: string;
  seedDocuments?: string[];
  generateReport?: boolean;
}

interface SimulationResult {
  simulation_id: string;
  status: string;
  rounds_completed: number;
  total_actions: number;
  summary: string;
}

class ChimeraClient {
  constructor(private baseUrl: string = 'http://localhost:8016') {}

  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    // implementation
  }

  async startSimulation(options: SimulationOptions): Promise<SimulationResult> {
    // implementation
  }
}
```

## Related Documentation

- [API Endpoints Reference](../endpoints.md)
- [Data Models](../models.md)
- [Python Examples](./python.md)
- [curl Examples](./curl.md)
