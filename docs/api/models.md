# API Models and Schemas Reference

Complete reference for all data models used in the Chimera Simulation Engine API.

## Table of Contents

- [Request Models](#request-models)
  - [SimulationConfig](#simulationconfig)
  - [AgentGenerationRequest](#agentgenerationrequest)
  - [GraphBuildRequest](#graphbuildrequest)
- [Response Models](#response-models)
  - [SimulationResult](#simulationresult)
  - [AgentProfile](#agentprofile)
  - [GraphBuildResponse](#graphbuildresponse)
  - [HealthResponse](#healthresponse)
- [Nested Models](#nested-models)
  - [Entity](#entity)
  - [Relationship](#relationship)
  - [Fact](#fact)
  - [Graph](#graph)
  - [SimulationAction](#simulationaction)
  - [SimulationRound](#simulationround)
  - [SimulationTrace](#simulationtrace)
  - [ReportSection](#reportsection)
  - [Demographics](#demographics)
  - [BehavioralProfile](#behavioralprofile)
  - [Argument](#argument)
  - [DebateResult](#debateresult)
  - [Report](#report)
  - [ComprehensiveReport](#comprehensivereport)
  - [AgentResponse](#agentresponse)
- [Error Responses](#error-responses)
- [Enumerations](#enumerations)
  - [EntityType](#entitytype)
  - [RelationType](#relationtype)
  - [ActionType](#actiontype)
  - [MBTIType](#mbtitype)
  - [PoliticalLeaning](#politicalleaning)

---

## Request Models

### SimulationConfig

Configuration for running a simulation. Defines the parameters for agent behavior, scenario, and simulation duration.

**Endpoint:** `POST /api/simulate`

| Field | Type | Required | Description | Default |
|-------|------|----------|-------------|---------|
| `agent_count` | integer | No | Number of agents to simulate (1-1000) | `10` |
| `simulation_rounds` | integer | No | Number of simulation rounds to run (1-100) | `10` |
| `scenario_description` | string | Yes | Detailed description of the scenario to simulate | - |
| `scenario_topic` | string | No | Optional topic categorization for the scenario | `null` |
| `seed_documents` | array[string] | No | Initial documents to seed agent knowledge | `[]` |
| `generate_report` | boolean | No | Whether to generate a comprehensive report after simulation | `false` |

**Constraints:**
- `agent_count`: Must be between 1 and 1000 (inclusive)
- `simulation_rounds`: Must be between 1 and 100 (inclusive)
- `scenario_description`: Minimum 1 character, no maximum limit

**Example:**
```json
{
  "agent_count": 50,
  "simulation_rounds": 20,
  "scenario_description": "Discussion about remote work policies post-pandemic",
  "scenario_topic": "workplace policy",
  "seed_documents": [
    "Remote work increases productivity by 20%",
    "Office culture suffers with remote work"
  ],
  "generate_report": true
}
```

---

### AgentGenerationRequest

Request to generate diverse agent personas for use in simulations.

**Endpoint:** `POST /api/agents/generate`

| Field | Type | Required | Description | Default |
|-------|------|----------|-------------|---------|
| `count` | integer | Yes | Number of personas to generate (1-1000) | - |
| `seed` | integer | No | Random seed for reproducible generation | `null` |

**Constraints:**
- `count`: Must be between 1 and 1000 (inclusive)
- `seed`: Must be a valid integer if provided

**Example:**
```json
{
  "count": 25,
  "seed": 42
}
```

---

### GraphBuildRequest

Request to build a knowledge graph from provided documents.

**Endpoint:** `POST /api/graph/build`

| Field | Type | Required | Description | Default |
|-------|------|----------|-------------|---------|
| `documents` | array[string] | Yes | Documents to extract entities and relationships from | - |

**Constraints:**
- `documents`: Array must contain at least one document
- Each document should be a non-empty string

**Example:**
```json
{
  "documents": [
    "Climate change is causing rising sea levels globally.",
    "Renewable energy sources are becoming more cost-effective."
  ]
}
```

---

## Response Models

### SimulationResult

Results returned after a simulation completes. Contains summary statistics and action logs.

| Field | Type | Description |
|-------|------|-------------|
| `simulation_id` | string | Unique identifier for the simulation |
| `status` | string | Current status of the simulation (e.g., "completed", "failed") |
| `rounds_completed` | integer | Number of simulation rounds that finished |
| `total_actions` | integer | Total number of actions taken by all agents |
| `final_summary` | string | Narrative summary of simulation results |
| `action_log` | array[array[object]] | Detailed log of actions per round |
| `start_time` | float | Unix timestamp when simulation started |

**Example:**
```json
{
  "simulation_id": "sim_20250317_123456",
  "status": "completed",
  "rounds_completed": 10,
  "total_actions": 347,
  "final_summary": "Agents demonstrated diverse perspectives on remote work...",
  "action_log": [
    [
      {
        "agent_id": "agent_001",
        "action_type": "post",
        "content": "I believe remote work is the future...",
        "timestamp": "2025-03-17T12:34:56Z"
      }
    ]
  ],
  "start_time": 1710687296.123
}
```

---

### AgentProfile

Complete persona definition for a simulation agent. Includes personality, demographics, and behavioral traits.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for the agent |
| `mbti` | string | Myers-Briggs Type Indicator personality type |
| `demographics` | object | Demographic information (age, gender, education, etc.) |
| `behavioral` | object | Big Five personality traits scores |
| `political_leaning` | string | Political orientation category |
| `information_sources` | array[string] | Preferred news/information sources |
| `memory_capacity` | integer | Number of past interactions agent can recall |

**Example:**
```json
{
  "id": "agent_001",
  "mbti": "INTJ",
  "demographics": {
    "age": 34,
    "gender": "female",
    "education": "Masters",
    "occupation": "Data Scientist",
    "location": "San Francisco, CA",
    "income_level": "high"
  },
  "behavioral": {
    "openness": 0.85,
    "conscientiousness": 0.72,
    "extraversion": 0.31,
    "agreeableness": 0.45,
    "neuroticism": 0.38
  },
  "political_leaning": "center_left",
  "information_sources": [
    "Nature",
    "Science Daily",
    "ArXiv"
  ],
  "memory_capacity": 50
}
```

---

### GraphBuildResponse

Response from knowledge graph building operation.

| Field | Type | Description |
|-------|------|-------------|
| `graph_id` | string | Identifier for the created graph |
| `entities` | integer | Number of entities extracted |
| `relationships` | integer | Number of relationships found |

**Example:**
```json
{
  "graph_id": "temp_graph_1",
  "entities": 42,
  "relationships": 67
}
```

---

### HealthResponse

Response from health check endpoints.

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Health status ("healthy", "ready") |
| `service` | string | Service name |
| `version` | string | Service version |

**Example:**
```json
{
  "status": "healthy",
  "service": "simulation-engine",
  "version": "0.1.0"
}
```

---

## Nested Models

### Entity

Represents an entity in the knowledge graph.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for the entity |
| `type` | string | Entity type (person, organization, location, event, concept, policy) |
| `attributes` | object | Key-value pairs of entity attributes |
| `valid_at` | datetime | When this entity became valid |
| `invalid_at` | datetime (optional) | When this entity became invalid (if applicable) |

---

### Relationship

Represents a relationship between two entities in the knowledge graph.

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | ID of the source entity |
| `target` | string | ID of the target entity |
| `type` | string | Relationship type (knows, works_for, located_in, participated_in, related_to, influences) |
| `attributes` | object | Key-value pairs of relationship attributes |
| `valid_at` | datetime | When this relationship became valid |
| `invalid_at` | datetime (optional) | When this relationship became invalid (if applicable) |

---

### Fact

Represents a temporal fact in the knowledge graph.

| Field | Type | Description |
|-------|------|-------------|
| `subject` | string | Subject of the fact |
| `predicate` | string | Predicate/relationship |
| `object` | string | Object of the fact |
| `confidence` | float | Confidence score (0.0-1.0) |
| `valid_at` | datetime | When this fact became valid |
| `invalid_at` | datetime (optional) | When this fact became invalid (if applicable) |

---

### Graph

Complete knowledge graph containing entities, relationships, and facts.

| Field | Type | Description |
|-------|------|-------------|
| `entities` | array[Entity] | List of entities in the graph |
| `relationships` | array[Relationship] | List of relationships |
| `facts` | array[Fact] | List of temporal facts |
| `created_at` | datetime | Graph creation timestamp |
| `updated_at` | datetime | Last update timestamp |

---

### SimulationAction

A single action taken by an agent during simulation.

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | string | ID of the agent performing the action |
| `action_type` | string | Type of action (post, reply, like, retweet, follow, quote) |
| `content` | string | Action content/text |
| `timestamp` | datetime | When the action occurred |
| `metadata` | object | Additional action metadata |

---

### SimulationRound

A round of simulation containing multiple agent actions.

| Field | Type | Description |
|-------|------|-------------|
| `round_number` | integer | Round sequence number |
| `actions` | array[SimulationAction] | All actions in this round |
| `agent_states` | object | Agent state snapshots at round end |

---

### SimulationTrace

Complete trace of a simulation run with all rounds and knowledge graph context.

| Field | Type | Description |
|-------|------|-------------|
| `simulation_id` | string | Unique simulation identifier |
| `topic` | string | Simulation topic |
| `rounds` | array[SimulationRound] | All simulation rounds |
| `knowledge_graph_entities` | array[string] | Entity IDs from knowledge graph |
| `knowledge_graph_relationships` | array[string] | Relationship IDs from knowledge graph |
| `started_at` | datetime | Simulation start time |
| `completed_at` | datetime (optional) | Simulation completion time |
| `metadata` | object | Additional trace metadata |

---

### ReportSection

A section of a generated report with confidence scoring.

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Section title |
| `content` | string | Section content |
| `confidence` | float | Confidence score (0.0-1.0) |
| `sources` | array[string] | Source references |

**Constraints:**
- `confidence`: Automatically clamped to range [0.0, 1.0]

---

### Demographics

Demographic characteristics of an agent. Part of `AgentProfile`.

| Field | Type | Description |
|-------|------|-------------|
| `age` | integer | Agent's age in years |
| `gender` | string | Gender identity |
| `education` | string | Highest education level |
| `occupation` | string | Current occupation |
| `location` | string | Geographic location |
| `income_level` | string | Income bracket (e.g., "low", "medium", "high") |

---

### BehavioralProfile

Big Five personality traits scores. Part of `AgentProfile`.

All scores range from 0.0 to 1.0.

| Field | Type | Description |
|-------|------|-------------|
| `openness` | float | Openness to experience (creativity, curiosity) |
| `conscientiousness` | float | Self-discipline, organization, dependability |
| `extraversion` | float | Sociability, assertiveness, energy |
| `agreeableness` | float | Cooperation, compassion, trust |
| `neuroticism` | float | Emotional stability, anxiety倾向 |

---

### Argument

A single argument in a ForumEngine debate.

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | string | ID of agent making the argument |
| `content` | string | Argument text |
| `stance` | float | Position on topic (-1.0 oppose to 1.0 support) |
| `reasoning` | string | Rationale behind the stance |
| `created_at` | datetime (optional) | Timestamp when argument was created |

**Constraints:**
- `stance`: Automatically clamped to range [-1.0, 1.0]

---

### DebateResult

Results from a multi-agent ForumEngine debate.

| Field | Type | Description |
|-------|------|-------------|
| `topic` | string | Debate topic |
| `arguments` | array[Argument] | All arguments presented |
| `consensus_score` | float | Agreement level (0-1, higher = more consensus) |
| `confidence_interval` | tuple[float, float] | Lower and upper bounds of confidence |
| `summary` | string | Narrative summary of debate |

---

### Report

A comprehensive ReACT ReportAgent report.

| Field | Type | Description |
|-------|------|-------------|
| `simulation_id` | string | Associated simulation ID |
| `generated_at` | datetime | When report was generated |
| `executive_summary` | object | Summary section with title, content, confidence |
| `findings` | array[object] | List of finding sections |
| `recommendations` | array[object] | List of recommendation sections |
| `confidence_interval` | tuple[float, float] | Statistical confidence bounds |
| `metadata` | object | Additional report metadata |

Each section contains:
- `title`: Section title
- `content`: Section content
- `confidence`: Confidence score (0-1)
- `sources`: List of source references

---

### ComprehensiveReport

Complete report combining ForumEngine debate results and ReACT analysis.

| Field | Type | Description |
|-------|------|-------------|
| `simulation_id` | string | Associated simulation ID |
| `generated_at` | datetime | When report was generated |
| `topic` | string | Simulation/debate topic |
| `executive_summary` | object | ReACT summary section |
| `findings` | array[object] | ReACT finding sections |
| `recommendations` | array[object] | ReACT recommendation sections |
| `debate_summary` | string | ForumEngine debate summary |
| `consensus_score` | float | Debate agreement level |
| `debate_arguments` | array[Argument] | All debate arguments |
| `confidence_interval` | tuple[float, float] | Statistical confidence bounds |
| `overall_confidence` | float | Combined confidence score |
| `forum_rounds` | integer | Number of forum debate rounds |
| `react_iterations` | integer | Number of ReACT iterations |
| `metadata` | object | Additional metadata |

---

### AgentResponse

Response from interviewing an agent post-simulation.

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | string | ID of the interviewed agent |
| `question` | string | Question asked to the agent |
| `response` | string | Agent's response |
| `context` | object | Context including memory snippets, rounds covered |
| `timestamp` | datetime | When response was generated |

---

## Error Responses

The API uses standard HTTP status codes and returns error details in JSON format.

### 400 Bad Request

Invalid request parameters or malformed data.

**Example:**
```json
{
  "detail": "Count must be between 1 and 1000"
}
```

**Common causes:**
- Agent count outside valid range (1-1000)
- Simulation rounds outside valid range (1-100)
- Missing required fields

---

### 422 Validation Error

Request schema validation failed. Detailed field-level errors provided.

**Example:**
```json
{
  "detail": [
    {
      "loc": ["body", "agent_count"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

**Common causes:**
- Wrong data type for field
- String validation failures
- Enum value mismatches

---

### 500 Internal Server Error

Unexpected server error during request processing.

**Example:**
```json
{
  "detail": "Internal server error"
}
```

**Common causes:**
- Database connection failures
- LLM API errors
- Unhandled exceptions

---

### 503 Service Unavailable

Required service not initialized or unavailable.

**Example:**
```json
{
  "detail": "Simulation service not initialized"
}
```

**Common causes:**
- Simulation runner not initialized
- Graph service not ready
- External dependency unavailable

---

## Enumerations

### EntityType

Types of entities in the knowledge graph.

| Value | Description |
|-------|-------------|
| `person` | Individual person |
| `organization` | Company, institution, or group |
| `location` | Geographic location |
| `event` | Occurrence or incident |
| `concept` | Abstract concept or idea |
| `policy` | Policy or regulation |

---

### RelationType

Types of relationships between entities in the knowledge graph.

| Value | Description |
|-------|-------------|
| `knows` | Acquaintance or familiarity |
| `works_for` | Employment relationship |
| `located_in` | Geographic containment |
| `participated_in` | Event participation |
| `related_to` | General relationship |
| `influences` | Causal or influential relationship |

---

### ActionType

Social action types from the OASIS framework.

| Value | Description |
|-------|-------------|
| `post` | Create new content |
| `reply` | Respond to existing content |
| `retweet` | Share existing content |
| `like` | Express approval |
| `follow` | Subscribe to agent |
| `quote` | Comment while sharing |

---

### MBTIType

Myers-Briggs Type Indicator personality types.

| Value | Description |
|-------|-------------|
| `INTJ` | Architect - Imaginative and strategic thinkers |
| `INTP` | Logician - Innovative inventors with a thirst for knowledge |
| `ENTJ` | Commander - Bold, imaginative, and strong-willed leaders |
| `ENTP` | Debater - Smart and curious thinkers who cannot resist an intellectual challenge |
| `INFJ` | Advocate - Quiet and mystical, yet very inspiring and tireless idealists |
| `INFP` | Mediator - Poetic, kind and altruistic, always eager to help a good cause |
| `ENFJ` | Protagonist - Charismatic and inspiring leaders, able to mesmerize their listeners |
| `ENFP` | Campaigner - Enthusiastic, creative and sociable free spirits |
| `ISTJ` | Logistician - Practical and fact-minded individuals, whose reliability cannot be doubted |
| `ISFJ` | Defender - Very dedicated and warm protectors, always ready to defend their loved ones |
| `ESTJ` | Executive - Excellent administrators, unsurpassed at managing things or people |
| `ESFJ` | Consul - Extraordinarily caring, social and popular people, always eager to help |
| `ISTP` | Virtuoso - Bold and practical experimenters, masters of all kinds of tools |
| `ISFP` | Adventurer - Flexible and charming artists, always ready to explore and experience something new |
| `ESTP` | Entrepreneur - Smart, energetic and very perceptive people, who truly enjoy living on the edge |
| `ESFP` | Entertainer - Spontaneous, energetic and enthusiastic people - life is never boring around them |

---

### PoliticalLeaning

Political orientation categories.

| Value | Description |
|-------|-------------|
| `far_left` | Far-left political orientation |
| `left` | Left-leaning political orientation |
| `center_left` | Center-left political orientation |
| `center` | Centrist/moderate political orientation |
| `center_right` | Center-right political orientation |
| `right` | Right-leaning political orientation |
| `far_right` | Far-right political orientation |

---

## Type Formats

### datetime

DateTime fields use ISO 8601 format with timezone.

**Format:** `YYYY-MM-DDTHH:MM:SSZ`

**Example:** `2025-03-17T12:34:56Z`

### float

Floating-point numbers follow IEEE 754 double precision.

**Range:** Platform-dependent, typically ±1.7976931348623157E+308

**Precision:** Approximately 15-17 decimal digits

### integer

Integer fields are 64-bit signed integers.

**Range:** -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807

---

## Validation Rules

### Numeric Constraints

- `agent_count`: 1 ≤ value ≤ 1000
- `simulation_rounds`: 1 ≤ value ≤ 100
- `behavioral` traits: 0.0 ≤ value ≤ 1.0
- `stance` (Argument): -1.0 ≤ value ≤ 1.0 (auto-clamped)
- `confidence`: 0.0 ≤ value ≤ 1.0 (auto-clamped)

### String Constraints

- `id` fields: Non-empty, typically formatted as `type_timestamp` or `type_number`
- `scenario_description`: Minimum 1 character
- `mbti`: Must match valid MBTIType enum value
- `political_leaning`: Must match valid PoliticalLeaning enum value

### Array Constraints

- `seed_documents`: Can be empty, no maximum size
- `action_log`: Array of arrays, one per round
- `information_sources`: Can be empty, no maximum size

---

## Related Documentation

- [API Endpoints Reference](./endpoints.md) - Complete API endpoint documentation
- [Usage Examples](./examples/) - Code examples for common operations
- [Getting Started](../guides/getting-started.md) - Quick start guide
- [System Architecture](../architecture/system-design.md) - Overall system design

---

**Last Updated:** 2026-03-18

**API Version:** 0.1.0
