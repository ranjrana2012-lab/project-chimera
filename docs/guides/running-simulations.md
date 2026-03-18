# Running Simulations

> **Version:** 1.0.0
> **Last Updated:** 2026-03-18
> **Audience:** Developers, Researchers, Policy Analysts
> **Estimated Reading Time:** 20 minutes

Learn how to configure, run, and interpret simulations with the Chimera Simulation Engine. This guide covers scenario configuration, agent population setup, document preparation for knowledge graphs, and result interpretation.

## Overview

The Chimera Simulation Engine enables you to test "what-if" scenarios by simulating diverse agent populations interacting within a defined context. Each simulation follows a five-stage pipeline:

1. **Knowledge Graph Construction** - Extract entities and relationships from seed documents
2. **Environment Setup** - Generate diverse agent personas with unique characteristics
3. **Simulation Execution** - Run multi-agent simulation rounds
4. **Report Generation** - Synthesize results into comprehensive reports
5. **Deep Interaction** - Query individual agents for detailed insights

## Simulation Configuration

### Basic Configuration Structure

All simulations start with a configuration object that defines the scenario parameters:

```json
{
  "agent_count": 100,
  "simulation_rounds": 10,
  "scenario_description": "A carbon tax of $50/ton is introduced. How does this affect consumer behavior, business decisions, and political support over 2 years?",
  "scenario_type": "policy_analysis",
  "scenario_topic": "Carbon Tax Impact Assessment",
  "seed_documents": [
    "Carbon pricing mechanisms and their economic effects...",
    "Historical data on carbon tax implementation..."
  ],
  "generate_report": true
}
```

### Configuration Parameters

| Parameter | Type | Required | Range | Description | Recommendation |
|-----------|------|----------|-------|-------------|----------------|
| `agent_count` | integer | Yes | 1-1000 | Number of agents in simulation | Start with 10-50 for testing, use 100-500 for production |
| `simulation_rounds` | integer | Yes | 1-100 | Number of simulation rounds | 5-10 for quick results, 20-50 for thorough analysis |
| `scenario_description` | string | Yes | - | Human-readable scenario context | Be specific and detailed (50-500 words) |
| `scenario_type` | string | No | - | Type for routing and analysis | `policy_analysis`, `social_dynamics`, `organizational`, `general` |
| `scenario_topic` | string | No | - | Short topic label | Used in reports and metrics |
| `seed_documents` | array | No | - | Documents for knowledge graph | 1-10 documents, 500-5000 words each |
| `generate_report` | boolean | No | - | Generate comprehensive report | `true` for final analysis, `false` for testing |

### Parameter Selection Guidelines

#### Agent Count

**Small (1-20 agents)**
- **Use Case:** Initial testing, hypothesis validation, quick iterations
- **Pros:** Fast execution, low cost, easy to analyze individual behavior
- **Cons:** Limited diversity, may not capture emergent behaviors
- **Example:** Testing a new policy concept before full simulation

```json
{
  "agent_count": 10,
  "simulation_rounds": 5
}
```

**Medium (20-100 agents)**
- **Use Case:** Standard analysis, diversity requirements, moderate complexity
- **Pros:** Good balance of diversity and speed, reliable results
- **Cons:** May miss rare edge cases
- **Example:** Policy impact analysis with diverse demographics

```json
{
  "agent_count": 50,
  "simulation_rounds": 15
}
```

**Large (100-1000 agents)**
- **Use Case:** Complex scenarios, population-level analysis, comprehensive coverage
- **Pros:** Maximum diversity, captures edge cases, statistically robust
- **Cons:** Expensive, slower execution, complex analysis
- **Example:** National policy assessment, social dynamics research

```json
{
  "agent_count": 500,
  "simulation_rounds": 30
}
```

#### Simulation Rounds

**Quick Analysis (1-10 rounds)**
- **Use Case:** Rapid prototyping, initial trends, concept validation
- **Pros:** Fast results, low cost
- **Cons:** May miss long-term dynamics

```json
{
  "simulation_rounds": 5
}
```

**Standard Analysis (10-30 rounds)**
- **Use Case:** Most scenarios, policy assessment, trend identification
- **Pros:** Balances speed and depth, captures medium-term dynamics
- **Cons:** May miss very long-term effects

```json
{
  "simulation_rounds": 20
}
```

**Deep Analysis (30-100 rounds)**
- **Use Case:** Long-term forecasting, complex system dynamics, research
- **Pros:** Captures long-term trends, system convergence
- **Cons:** Expensive, time-consuming

```json
{
  "simulation_rounds": 50
}
```

## Scenario Types

### Policy Analysis

Analyze the impact of policy decisions on diverse populations.

```json
{
  "agent_count": 100,
  "simulation_rounds": 20,
  "scenario_description": "A city introduces a congestion pricing policy of $15 per day for downtown driving during peak hours (7-10 AM, 4-7 PM). Exemptions apply to emergency vehicles and public transit. Revenue will fund public transportation improvements. Analyze impacts on: commuter behavior, local business revenue, environmental quality, and public support over 12 months.",
  "scenario_type": "policy_analysis",
  "scenario_topic": "Urban Congestion Pricing Assessment"
}
```

**Key Elements:**
- Specific policy details (amount, timing, exemptions)
- Affected stakeholders (commuters, businesses, residents)
- Timeframe (immediate, short-term, long-term)
- Revenue use or funding mechanism
- Clear analysis objectives

### Social Dynamics

Study information spread, opinion formation, and social influence.

```json
{
  "agent_count": 200,
  "simulation_rounds": 30,
  "scenario_description": "A new social media platform gains popularity among younger demographics (18-35). The platform uses an algorithm that prioritizes emotionally engaging content over factual accuracy. Track how information about a controversial topic (e.g., climate policy) spreads through the network, examining: echo chamber formation, opinion polarization, misinformation propagation, and cross-demographic information exchange.",
  "scenario_type": "social_dynamics",
  "scenario_topic": "Social Media Information Spread"
}
```

**Key Elements:**
- Network structure and dynamics
- Information propagation mechanisms
- Demographic segments
- Measurement objectives (polarization, echo chambers, etc.)
- Platform or medium characteristics

### Organizational Behavior

Analyze team dynamics, decision-making, and organizational change.

```json
{
  "agent_count": 25,
  "simulation_rounds": 15,
  "scenario_description": "A mid-sized technology company (200 employees) announces a permanent remote work policy. Teams can choose fully remote, hybrid (2-3 days office), or fully in-office work. The company provides a stipend for home office setup. Analyze impacts on: team collaboration patterns, employee satisfaction and retention, productivity metrics, and innovation output over 6 months.",
  "scenario_type": "organizational",
  "scenario_topic": "Remote Work Policy Impact"
}
```

**Key Elements:**
- Organizational context and size
- Policy options and flexibility
- Support mechanisms or resources
- Success metrics
- Implementation timeline

## Agent Population Setup

### Understanding Agent Profiles

Each agent is defined by a comprehensive profile that influences their behavior:

```json
{
  "id": "agent_0042",
  "mbti": "INTJ",
  "demographics": {
    "age": 34,
    "gender": "female",
    "education": "master",
    "occupation": "data_scientist",
    "location": "urban",
    "income_level": "high"
  },
  "behavioral": {
    "openness": 0.8,
    "conscientiousness": 0.7,
    "extraversion": 0.3,
    "agreeableness": 0.5,
    "neuroticism": 0.4
  },
  "political_leaning": "center_left",
  "information_sources": ["academic_journals", "news_analysis", "podcasts"],
  "memory_capacity": 150
}
```

### Agent Attributes

#### MBTI Personality Types

The simulation uses all 16 Myers-Briggs Type Indicator types:

- **Analysts:** INTJ, INTP, ENTJ, ENTP
- **Diplomats:** INFJ, INFP, ENFJ, ENFP
- **Sentinels:** ISTJ, ISFJ, ESTJ, ESFJ
- **Explorers:** ISTP, ISFP, ESTP, ESFP

Each type influences:
- Decision-making style (thinking vs. feeling)
- Information processing (sensing vs. intuition)
- Energy direction (introversion vs. extraversion)
- Structure preference (judging vs. perceiving)

#### Behavioral Traits (OCEAN Model)

- **Openness:** Curiosity, creativity, preference for novelty (0.0-1.0)
- **Conscientiousness:** Organization, discipline, reliability (0.0-1.0)
- **Extraversion:** Sociability, assertiveness, energy level (0.0-1.0)
- **Agreeableness:** Cooperation, empathy, conflict avoidance (0.0-1.0)
- **Neuroticism:** Emotional stability, anxiety reactivity (0.0-1.0)

#### Demographics

- **Age:** 18-75 (influences experience and perspective)
- **Gender:** male, female, non_binary, prefer_not_to_say
- **Education:** high_school, bachelor, master, phd
- **Occupation:** Influences expertise and worldview
- **Location:** urban, suburban, rural (affects information access)
- **Income Level:** low, medium, high, very_high

#### Political Leaning

Seven-point spectrum from far_left to far_right, influencing:
- Policy preferences
- Information source selection
- Interpretation of events
- Willingness to compromise

#### Information Sources

Agents preferentially consume information from:
- twitter, reddit, news_website, social_media
- podcasts, youtube, traditional_media, forums

This affects:
- Information quality
- Exposure to diverse viewpoints
- Speed of information uptake

### Generating Custom Agent Populations

For controlled experiments, you can generate agent populations with specific characteristics:

```bash
curl -X POST http://localhost:8016/api/v1/agents/generate \
  -H "Content-Type: application/json" \
  -d '{
    "count": 50,
    "seed": 42,
    "diversity_config": {
      "mbti_distribution": "balanced",
      "political_spectrum": "full",
      "age_range": [25, 65],
      "urban_ratio": 0.7
    }
  }'
```

**Note:** Custom diversity configurations are planned for Phase 2. Currently, agents are generated with balanced distributions across all attributes.

## Document Preparation for Knowledge Graphs

Seed documents provide contextual knowledge that agents can reference during simulations. The knowledge graph extraction process identifies:

### What Gets Extracted

**Entities:**
- People, organizations, locations
- Concepts, policies, events
- Technologies, systems, processes

**Relationships:**
- Causal links (X causes Y)
- Temporal sequences (X precedes Y)
- Hierarchical structures (X is part of Y)
- Associations (X is related to Y)

**Temporal Facts:**
- Time-bound events and trends
- Historical context
- Future projections

### Best Practices for Seed Documents

#### 1. Quality Over Quantity

**Good:**
```
The carbon tax of $50 per metric ton was implemented in British Columbia in 2008.
Studies show it reduced greenhouse gas emissions by 5-15% without harming economic growth.
Revenue is returned to citizens through tax cuts.
```

**Poor:**
```
Carbon tax is bad. It hurts economy. People don't like it.
```

#### 2. Include Specific Details

Include:
- Specific numbers, dates, and quantities
- Causal mechanisms and explanations
- Multiple perspectives and viewpoints
- Historical examples and case studies
- Uncertainties and limitations

#### 3. Structure for Clarity

Use clear, well-structured text:
- Separate paragraphs for distinct concepts
- Topic sentences and supporting details
- Logical flow and transitions
- Concrete examples and evidence

#### 4. Document Length

**Per Document:**
- Minimum: 200 words (too short lacks context)
- Optimal: 500-2000 words (rich context)
- Maximum: 5000 words (beyond this, consider splitting)

**Total Collection:**
- Minimum: 1 document
- Optimal: 3-5 documents (diverse perspectives)
- Maximum: 10 documents (beyond this, processing cost increases)

### Example Seed Documents

**Document 1: Policy Background**
```
Carbon Pricing Overview
=======================
Carbon pricing is an economic instrument that puts a price on carbon emissions.
Two main approaches exist:
1. Carbon Tax: Direct price per ton of CO2 emitted
2. Cap-and-Trade: Market for emission permits

British Columbia implemented a $10/ton carbon tax in 2008, rising to $50/ton by 2021.
Results from the first 10 years:
- GHG emissions decreased by 5-15%
- GDP growth matched national average
- No significant employment impacts
- Revenue returned through income tax cuts

Key mechanisms:
- Price signal encourages low-carbon alternatives
- Revenue recycling maintains economic competitiveness
- Gradual increase allows adaptation
```

**Document 2: Stakeholder Perspectives**
```
Stakeholder Views on Carbon Pricing
===================================
Business Community:
- Small businesses concerned about cost increases
- Large corporations prefer predictability over regulation
- Industry associations support revenue-neutral approaches

Environmental Groups:
- Generally support carbon pricing as effective policy
- Some argue prices are too low to drive transformation
- Emphasize need for complementary policies

Public Opinion:
- Support increases when revenue is returned to citizens
- Concerns about cost of living impacts
- Preference for "fee and dividend" approach
- Higher support among younger demographics

Academic Research:
- Consensus on effectiveness for reducing emissions
- Debate over optimal price level and escalation rate
- Mixed evidence on competitiveness impacts
```

**Document 3: Implementation Considerations**
```
Carbon Tax Implementation Design
=================================
Rate Structure:
- Start low ($10-20/ton) and increase gradually
- Escalation rate of 5-10% annually
- Price floor to maintain predictability
- Exemptions for trade-exposed industries

Revenue Use Options:
1. Return to citizens (dividends or tax cuts)
2. Fund green infrastructure and R&D
3. Reduce other taxes (revenue-neutral)
4. Support affected workers and communities

Administrative Design:
- Upstream collection (fewer points of regulation)
- Border adjustments to prevent leakage
- Complementary policies for hard-to-abate sectors
- Regular review and adjustment mechanisms

Equity Considerations:
- Low-income households spend higher proportion on energy
- Rural households may have fewer alternatives
- Revenue recycling can address regressivity
- Just Transition support for affected workers
```

### Building Knowledge Graphs

Once you've prepared your documents, build the knowledge graph:

```bash
curl -X POST http://localhost:8016/api/v1/graph/build \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      "Carbon Pricing Overview\n===================\nCarbon pricing is an economic instrument...",
      "Stakeholder Views on Carbon Pricing\n===================================\nBusiness Community:...",
      "Carbon Tax Implementation Design\n===================================\nRate Structure:..."
    ]
  }'
```

**Response:**
```json
{
  "graph_id": "graph_carbon_tax_2024",
  "entities": 47,
  "relationships": 63,
  "extraction_method": "llm"
}
```

The `graph_id` can be referenced in simulations to provide agents with this contextual knowledge.

## Running Simulations

### Starting a Simulation

```bash
curl -X POST http://localhost:8016/api/v1/simulation/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "agent_count": 100,
    "simulation_rounds": 20,
    "scenario_description": "A carbon tax of $50/ton is introduced...",
    "scenario_type": "policy_analysis",
    "generate_report": true
  }'
```

**Response:**
```json
{
  "simulation_id": "sim_550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "rounds_completed": 20,
  "total_actions": 2000,
  "summary": "Simulation Summary\n==================\nScenario: A carbon tax of $50/ton is introduced...\nAgents: 100\nRounds: 20\nTotal Actions: 2000\n\nThe simulation completed successfully. Agents showed diverse responses based on their demographic and psychological profiles..."
}
```

Save the `simulation_id` for later reference and report generation.

### Monitoring Simulation Execution

For long-running simulations, you can monitor progress:

```bash
# Check simulation status
SIMULATION_ID="sim_550e8400-e29b-41d4-a716-446655440000"
curl http://localhost:8016/api/v1/simulation/${SIMULATION_ID}/status
```

**Response:**
```json
{
  "simulation_id": "sim_550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "rounds_completed": 15,
  "total_rounds": 20,
  "current_round": 16,
  "actions_so_far": 1500
}
```

### Synchronous vs Asynchronous Execution

**Current Implementation (Phase 1):**
- Simulations run synchronously
- Results returned in initial response
- Best for simulations completing in < 60 seconds

**Planned (Phase 2):**
- Asynchronous execution for long simulations
- WebSocket updates for real-time progress
- Callbacks or webhooks for completion notification

## Interpreting Results

### Understanding the Response Structure

```json
{
  "simulation_id": "sim_550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "rounds_completed": 20,
  "total_actions": 2000,
  "start_time": 1640995200.0,
  "summary": "Simulation Summary...",
  "action_log": [[...], [...], ...]
}
```

### Status Values

- **completed** - Simulation finished successfully
- **failed** - Simulation encountered an error
- **running** - Simulation is in progress (async mode)

### The Summary Section

The summary provides a high-level overview:

```
Simulation Summary
==================
Scenario: A carbon tax of $50/ton is introduced...
Agents: 100
Rounds: 20
Total Actions: 2000

This is a Phase 0 placeholder summary.
Phase 1 will use ReACT ReportAgent for detailed analysis.
```

**Phase 1 Enhancement:**
The summary will include:
- Overall sentiment trends
- Key consensus points
- Notable patterns and anomalies
- Confidence intervals
- Agent behavior clusters

### Action Log Analysis

The action log contains detailed records of each agent action in each round:

```json
[
  [
    {
      "agent_id": "agent_0001",
      "round": 0,
      "action_type": "post",
      "backend_used": "local",
      "timestamp": "2024-03-18T10:30:00Z"
    },
    ...
  ],
  ...
]
```

**Action Types:**
- **post** - Create new content or statement
- **reply** - Respond to existing content
- **retweet** - Share or amplify existing content
- **like** - Express approval or agreement
- **follow** - Connect with another agent
- **quote** - Share with commentary

### Comprehensive Reports

When `generate_report: true`, the simulation produces a comprehensive report including:

#### Executive Summary
- High-level findings
- Key conclusions
- Confidence levels

#### Detailed Analysis
- Agent behavior patterns
- Opinion dynamics
- Consensus and disagreement areas
- Temporal trends

#### Recommendations
- Policy implications
- Implementation considerations
- Risk factors
- Success metrics

#### Debate Summary
- Multi-agent forum results
- Argument analysis
- Consensus scoring
- Confidence intervals

**Example Report Structure:**
```json
{
  "simulation_id": "sim_550e8400-e29b-41d4-a716-446655440000",
  "generated_at": "2024-03-18T10:35:00Z",
  "topic": "Carbon Tax Impact Assessment",
  "executive_summary": {
    "overview": "The simulation indicates moderate public support...",
    "key_findings": [
      "Carbon tax acceptance increases with revenue recycling",
      "Low-income households require targeted support",
      "Business concerns focus on competitiveness"
    ],
    "confidence": 0.78
  },
  "findings": [
    {
      "category": "Public Opinion",
      "summary": "Support varies by demographic and policy design",
      "evidence": "67% of agents support with dividend, 42% without",
      "confidence": 0.85
    }
  ],
  "recommendations": [
    {
      "action": "Implement revenue-neutral design with citizen dividends",
      "rationale": "Increases public support while maintaining effectiveness",
      "priority": "high",
      "confidence": 0.82
    }
  ],
  "confidence_interval": [0.72, 0.84],
  "overall_confidence": 0.78
}
```

### Confidence Intervals

Reports include confidence intervals to indicate result reliability:

- **High Confidence (0.8-1.0):** Strong consensus, reliable results
- **Medium Confidence (0.6-0.8):** Moderate consensus, results likely reliable
- **Low Confidence (0.4-0.6):** Weak consensus, treat results cautiously
- **Very Low Confidence (0.0-0.4):** High disagreement, results uncertain

**Interpreting Confidence:**
- Narrow intervals (e.g., [0.75, 0.81]) indicate high certainty
- Wide intervals (e.g., [0.55, 0.85]) indicate high variability
- Use confidence levels to weigh recommendations
- Consider additional analysis for low-confidence results

## Best Practices

### 1. Start Small, Scale Up

Begin with small simulations to validate your scenario:

```json
{
  "agent_count": 10,
  "simulation_rounds": 5,
  "scenario_description": "Test scenario..."
}
```

Review results, refine scenario, then scale up:
```json
{
  "agent_count": 100,
  "simulation_rounds": 20
}
```

### 2. Use Specific, Detailed Scenarios

**Poor:**
```
Test a new tax policy
```

**Good:**
```
A carbon tax of $50/ton is introduced on fossil fuels. Revenue is returned to citizens
as quarterly dividends. The tax increases by $5/ton annually. Analyze impacts over 5 years
on: consumer behavior, business investment, emissions, and political support among
demographic groups (urban/rural, income levels, age groups).
```

### 3. Provide Diverse Seed Documents

Include multiple perspectives:
- Academic research
- Government reports
- Industry analyses
- Stakeholder position papers
- Historical case studies

### 4. Enable Reports for Production Runs

Set `generate_report: true` for:
- Final analysis
- Stakeholder presentations
- Policy recommendations
- Research documentation

Set `generate_report: false` for:
- Initial testing
- Scenario validation
- Quick iterations

### 5. Monitor Token Usage

Check metrics to track costs:

```bash
curl http://localhost:8016/metrics | grep simulation
```

**Output:**
```
simulations_total{scenario_type="policy_analysis"} 42.0
simulation_duration_seconds_bucket{scenario_type="policy_analysis",le="1.0"} 38.0
```

### 6. Use Scenario Types Appropriately

Choose the right scenario type for better routing and analysis:

- `policy_analysis` - Government policies, regulations, laws
- `social_dynamics` - Information spread, opinion formation, social networks
- `organizational` - Corporate decisions, team dynamics, workplace policies
- `general` - Exploratory scenarios, mixed domains

### 7. Leverage Reproducibility

Use seeds for reproducible agent populations:

```json
{
  "count": 100,
  "seed": 42
}
```

Same seed = same agent population, enabling:
- Comparative analysis
- Debugging
- Validation studies
- Controlled experiments

### 8. Document Your Scenarios

Maintain a scenario library with:
- Scenario description
- Configuration parameters
- Seed documents
- Results and interpretations
- Lessons learned

## Common Pitfalls and Solutions

### Pitfall 1: Too Few Agents

**Problem:** Less than 10 agents may not show diverse behavior or meaningful patterns.

**Solution:** Use at least 20-50 agents for meaningful results, 100+ for robust analysis.

```json
{
  "agent_count": 50,  // Not 5
  "simulation_rounds": 15
}
```

### Pitfall 2: Too Many Rounds

**Problem:** More than 50 rounds can be expensive and may not add value.

**Solution:** Start with 10-20 rounds, analyze results, increase if necessary.

```json
{
  "agent_count": 100,
  "simulation_rounds": 20  // Not 100
}
```

### Pitfall 3: Vague Scenarios

**Problem:** Agents may behave unpredictably or produce inconsistent results.

**Solution:** Provide clear context, constraints, and objectives.

**Poor:**
```
Test the impact of a new policy
```

**Good:**
```
A carbon tax of $50/ton on fossil fuels, with revenue returned as citizen dividends.
Tax increases by $5/ton annually. Analyze impacts on: consumer behavior (gasoline demand,
vehicle purchases), business decisions (investment, pricing), emissions, and political
support among urban/rural and high/low-income groups over 3 years.
```

### Pitfall 4: Ignoring Confidence Intervals

**Problem:** Treating all results as equally certain, leading to overconfident decisions.

**Solution:** Check confidence levels, treat low-confidence results cautiously.

```json
{
  "overall_confidence": 0.78,
  "confidence_interval": [0.72, 0.84]
}
```

**Action:**
- High confidence (0.8+): Use results for decision-making
- Medium confidence (0.6-0.8): Consider results, gather additional evidence
- Low confidence (<0.6): Treat as preliminary, run additional simulations

### Pitfall 5: Insufficient Seed Documents

**Problem:** Agents lack contextual knowledge, leading to generic responses.

**Solution:** Provide 3-5 high-quality seed documents with specific details.

```json
{
  "seed_documents": [
    "Historical carbon tax implementation data from BC, Sweden, and France...",
    "Economic impact studies on carbon pricing...",
    "Public opinion surveys on carbon tax designs..."
  ]
}
```

### Pitfall 6: Wrong Scenario Type

**Problem:** Results don't match analysis needs or routing is suboptimal.

**Solution:** Choose appropriate scenario type.

- Policy decisions → `policy_analysis`
- Social media, information spread → `social_dynamics`
- Corporate, workplace → `organizational`
- Exploratory → `general`

### Pitfall 7: Not Reviewing Action Logs

**Problem:** Missing important patterns by only reading the summary.

**Solution:** Review action logs for detailed insights, especially for research or critical decisions.

```json
{
  "action_log": [[...], [...], ...]  // Review this!
}
```

### Pitfall 8: Ignoring Demographic Variation

**Problem:** Assuming all agents behave similarly, missing important subgroups.

**Solution:** Analyze results by demographic segments (age, location, income, etc.).

**Phase 2 Enhancement:**
Segmented analysis will be automated in reports.

### Pitfall 9: Single Simulation Runs

**Problem:** Treating one simulation as definitive, missing variability.

**Solution:** Run multiple simulations with different seeds, compare results.

```bash
# Run simulation with seed 42
curl -X POST http://localhost:8016/api/v1/simulation/simulate \
  -d '{"agent_count": 100, "simulation_rounds": 20, "seed": 42, ...}'

# Run simulation with seed 123
curl -X POST http://localhost:8016/api/v1/simulation/simulate \
  -d '{"agent_count": 100, "simulation_rounds": 20, "seed": 123, ...}'
```

### Pitfall 10: Misinterpreting Confidence

**Problem:** Assuming high confidence = truth, low confidence = error.

**Solution:** Understand what confidence means:

- **High confidence:** Agents strongly agree, but they could be wrong
- **Low confidence:** Agents disagree, but minority view could be correct

Use confidence as one factor alongside:
- Quality of seed documents
- Scenario specificity
- Real-world validation
- Expert review

## Advanced Techniques

### Comparative Analysis

Compare different policy options:

```bash
# Scenario A: Carbon tax with dividend
curl -X POST http://localhost:8016/api/v1/simulation/simulate \
  -d '{"scenario_description": "Carbon tax $50/ton with citizen dividends..."}'

# Scenario B: Carbon tax with tax cuts
curl -X POST http://localhost:8016/api/v1/simulation/simulate \
  -d '{"scenario_description": "Carbon tax $50/ton with income tax cuts..."}'

# Scenario C: Cap and trade
curl -X POST http://localhost:8016/api/v1/simulation/simulate \
  -d '{"scenario_description": "Cap-and-trade system with declining cap..."}'
```

Compare results across:
- Public support levels
- Economic impact projections
- Emissions reduction effectiveness
- Distributional effects

### Sensitivity Analysis

Test parameter sensitivity:

```bash
# Vary agent count
for count in 50 100 200; do
  curl -X POST http://localhost:8016/api/v1/simulation/simulate \
    -d "{\"agent_count\": $count, \"simulation_rounds\": 20, ...}"
done

# Vary simulation rounds
for rounds in 10 20 40; do
  curl -X POST http://localhost:8016/api/v1/simulation/simulate \
    -d "{\"agent_count\": 100, \"simulation_rounds\": $rounds, ...}"
done
```

### Scenario Stress Testing

Test extreme or edge cases:

```json
{
  "scenario_description": "Carbon tax of $200/ton (very high) with rapid implementation (3 months). Analyze system disruption, public backlash, and economic shocks."
}
```

Use to identify:
- Breaking points
- Non-linear responses
- Unexpected consequences
- Risk factors

### Iterative Refinement

Progressively refine scenarios:

1. **Initial run:** Basic scenario, small population
2. **Review:** Analyze results, identify gaps
3. **Refine:** Add details, adjust parameters
4. **Scale:** Increase population and rounds
5. **Validate:** Compare with real-world data
6. **Finalize:** Production run with report generation

## Performance and Cost Optimization

### Reduce LLM Costs

**Use Tiered Routing:**
```bash
# In .env
ENABLE_TIERED_ROUTING=true
LOCAL_LLM_RATIO=0.95
```

This routes 95% of requests to local LLMs, dramatically reducing costs while maintaining quality.

### Optimize Simulation Parameters

**For Testing:**
```json
{
  "agent_count": 10,
  "simulation_rounds": 5,
  "generate_report": false
}
```

**For Production:**
```json
{
  "agent_count": 100,
  "simulation_rounds": 20,
  "generate_report": true
}
```

### Cache and Reuse Results

Save simulation IDs and results to avoid re-running expensive simulations:

```bash
# Save results
curl http://localhost:8016/api/v1/simulation/${SIMULATION_ID}/result > results.json

# Reuse cached results instead of re-running
```

### Monitor Metrics

Regularly check metrics:

```bash
# Token usage
curl http://localhost:8016/metrics | grep token

# Simulation count and duration
curl http://localhost:8016/metrics | grep simulation

# Cost estimation
# (Cost per 1K tokens) × (Total tokens) = Total cost
```

## Troubleshooting

### Simulation Fails to Start

**Symptoms:** 503 Service Unavailable error

**Causes:**
- Simulation runner not initialized
- Dependencies not connected

**Solutions:**
```bash
# Check health status
curl http://localhost:8016/health/ready

# Check logs
docker-compose logs simulation-engine

# Restart service
docker-compose restart simulation-engine
```

### Poor Quality Results

**Symptoms:** Generic or nonsensical agent behavior

**Causes:**
- Vague scenario description
- Insufficient seed documents
- Too few agents

**Solutions:**
- Add specific details to scenario
- Provide 3-5 high-quality seed documents
- Increase agent count to 50+

### High Variability Between Runs

**Symptoms:** Very different results with same scenario

**Causes:**
- Random agent generation
- LLM temperature settings
- Too few agents/rounds

**Solutions:**
- Use fixed seed for reproducibility
- Increase agent count
- Increase simulation rounds
- Run multiple simulations and aggregate

### Slow Performance

**Symptoms:** Simulations take too long

**Causes:**
- Too many agents or rounds
- Remote LLM calls
- Network latency

**Solutions:**
- Reduce agent count or rounds for testing
- Enable tiered routing (95% local LLM)
- Check network connectivity to LLM providers
- Consider local-only mode for development

## Next Steps

Now that you understand how to run simulations effectively:

### Explore Advanced Features

- **Agent Interviews** (Phase 2) - Query individual agents post-simulation
- **Custom Agent Profiles** (Phase 2) - Create specific agent types
- **Batch Simulations** (Phase 2) - Run multiple scenarios in parallel
- **Real-Time Monitoring** (Phase 2) - WebSocket updates during simulation

### Deepen Your Understanding

- **[Architecture Overview](../architecture/system-design.md)** - System design and data flow
- **[Component Reference](../architecture/components.md)** - Component details
- **[API Reference](../api/endpoints.md)** - Complete API documentation
- **[Extending the Engine](extending-engine.md)** - Customization guide

### Apply to Your Domain

- **Policy Analysis** - Test policy designs before implementation
- **Social Research** - Study opinion dynamics and information spread
- **Organizational Design** - Plan organizational changes
- **Strategic Planning** - Explore strategic scenarios and contingencies

## Summary

The Chimera Simulation Engine enables sophisticated "what-if" scenario testing through:

1. **Flexible Configuration** - Adjust agent count, rounds, and scenario parameters
2. **Diverse Agent Populations** - Agents with unique personalities and demographics
3. **Knowledge Graph Context** - Seed documents provide rich contextual knowledge
4. **Comprehensive Reports** - Detailed analysis with confidence intervals
5. **Cost-Effective Execution** - Tiered LLM routing minimizes costs

**Key Best Practices:**
- Start small, scale up gradually
- Use specific, detailed scenario descriptions
- Provide high-quality seed documents
- Enable reports for production runs
- Monitor confidence intervals
- Run multiple simulations for robustness

By following this guide, you can effectively leverage the Chimera Simulation Engine for policy analysis, social dynamics research, organizational behavior studies, and strategic planning.

**Ready to dive deeper?** Check out the [API Reference](../api/endpoints.md) for complete endpoint documentation or the [Architecture Overview](../architecture/system-design.md) to understand the system design.
