# ADR-003: OpenClaw Skills Architecture

## Status
Accepted

## Date
2026-02-26

## Context
Project Chimera needs to coordinate multiple AI agents in complex pipelines. Options include:
- Monolithic orchestrator
- Service mesh with Istio
- Message queue orchestration
- Custom skill-based framework (OpenClaw)

## Decision
Use **OpenClaw** skill-based orchestration architecture.

### Rationale

**Pros:**
- Modular - skills can be added/updated independently
- Reusable - skills can be shared across projects
- Explicit - skill definitions as code (YAML)
- Flexible - supports sequential and parallel execution
- Observable - built-in tracing and metrics per skill
- Safe - approval gates for critical operations

**Cons:**
- Additional learning curve for team
- Custom framework (less community support than service mesh)
- Requires skill definitions maintenance

## Consequences

- Skills defined as YAML files in `skills/` directory
- OpenClaw Orchestrator coordinates skill execution
- Each service exposes `/invoke` endpoint
- Pipeline execution supports timeouts, retries, and fallbacks
- Skills can be versioned and cached independently
