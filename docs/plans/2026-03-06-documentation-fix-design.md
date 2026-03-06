# Documentation Fix Design

**Date:** March 6, 2026
**Status:** Design Approved
**Goal:** Add missing Configuration sections to API docs and fix version references

---

## Overview

Add missing `## Configuration` sections to 6 API documentation files using a template-based approach, and fix version reference issues in release notes.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TEMPLATE-BASED DOC FIX                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. EXTRACT TEMPLATE                                          │
│     ├── Read safety-filter.md (has complete structure)        │
│     ├── Extract ## Configuration section as template          │
│     └── Create reusable configuration template                 │
│            │                                                    │
│            ▼                                                    │
│  2. GATHER SERVICE DATA                                       │
│     ├── Read each service's .env.example                      │
│     ├── Read config.py if available                           │
│     └── Extract service-specific configuration                 │
│            │                                                    │
│            ▼                                                    │
│  3. GENERATE CONFIGURATION SECTIONS                           │
│     ├── Apply template with service data                      │
│     ├── Insert into each API doc at correct location          │
│     └── Ensure consistent formatting                          │
│            │                                                    │
│            ▼                                                    │
│  4. FIX VERSION REFERENCES                                    │
│     ├── Update release notes status (v0.5.0 → planned)        │
│     └── Create migration guide v0.3-to-v0.4.md                │
│            │                                                    │
│            ▼                                                    │
│  5. VERIFY AND COMMIT                                        │
│     ├── Check all docs have Endpoints + Configuration         │
│     ├── Commit changes                                         │
│     └── Push to GitHub                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Template Extractor Component
- Reads `docs/api/safety-filter.md`
- Extracts the `## Configuration` section
- Creates template with placeholders for service-specific values

### 2. Service Data Collector Component
- Scans each service directory for `.env.example` files
- Reads `config.py` from each service if available
- Extracts: port numbers, environment variables, default values

### 3. Configuration Generator Component
- Combines template with service-specific data
- Generates complete `## Configuration` section for each service
- Services: bsl-agent, captioning-agent, openclaw-orchestrator, operator-console, scenespeak-agent, sentiment-agent

### 4. Version Fixer Component
- Updates `docs/release-notes/v0.5.0.md` status from "current" to "planned"
- Creates `docs/migration/v0.3-to-v0.4.md` with key changes
- References existing release notes for content

### 5. Verification Component
- Checks all 6 updated docs have both `## Endpoints` and `## Configuration`
- Validates markdown syntax
- Generates summary report of changes

---

## Data Flow

```
┌──────────────────────┐
│  safety-filter.md    │
│  (Template Source)   │
└──────────┬───────────┘
           │ Extract ## Configuration
           ▼
┌──────────────────────┐
│  Config Template     │
│  (Structure + Placeholders)│
└──────────┬───────────┘
           │
           │ For each service (6 services)
           ▼
┌──────────────────────┐      ┌──────────────────────┐
│  .env.example         │ ───▶ │  Service Config       │
│  config.py            │      │  Data Extracted       │
└──────────┬───────────┘      └──────────┬───────────┘
           │                              │
           └──────────┬───────────────────┘
                      │ Combine
                      ▼
           ┌──────────────────────┐
           │  Generated ## Config │
           │  Section             │
           └──────────┬───────────┘
                      │ Insert into API doc
                      ▼
           ┌──────────────────────┐
           │  Updated API Doc     │
           │  (bsl-agent.md, etc.) │
           └──────────────────────┘
```

**Parallel Flow:**
```
┌──────────────────────┐
│  release-notes/v0.5.0.md │
│  (Update status)       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  migration/v0.3-to-v0.4.md │
│  (Create new)           │
└──────────────────────┘
```

---

## Error Handling

### Template Extraction Errors
- **safety-filter.md missing or changed**: Use fallback template structure based on standard API doc format
- **Configuration section not found**: Scan for alternative headers or build from .env.example

### Service Data Collection Errors
- **.env.example missing**: Skip service, log warning, use default placeholder values
- **config.py missing**: Continue with just .env.example data
- **Malformed env file**: Log specific line, skip that variable, continue with others

### Generation Errors
- **Template application fails**: Write minimal Configuration section with basic structure
- **File write permission denied**: Log error, continue with other services, report in summary

### Version Fix Errors
- **release-notes/v0.5.0.md not found**: Create with minimal content or skip if not critical
- **Migration guide creation fails**: Log error, note in report, don't block other changes

### Recovery Strategy
- Non-fatal errors: Log and continue (best-effort approach)
- Fatal errors: Stop, report, request manual intervention
- All errors logged to console and final summary report

---

## Testing & Verification

### Pre-Commit Verification

1. **Configuration Section Presence**
   ```bash
   for doc in docs/api/{bsl-agent,captioning-agent,openclaw-orchestrator,operator-console,scenespeak-agent,sentiment-agent}.md; do
     grep -q "## Configuration" "$doc" && echo "✓ $doc" || echo "✗ $doc missing Configuration"
   done
   ```

2. **Section Quality Check**
   - Each Configuration section has environment variables listed
   - Default values provided where applicable
   - Format matches safety-filter.md template

3. **Markdown Syntax Validation**
   ```bash
   for doc in docs/api/*.md; do
     grep -m1 "^## " "$doc"  # Verify headers
   done
   ```

### Version Fixes Verification
1. `docs/release-notes/v0.5.0.md` contains "planned" not "current"
2. `docs/migration/v0.3-to-v0.4.md` exists and has content

### Final Verification
- All 6 services now have Endpoints + Configuration sections
- No broken markdown links
- Git diff shows expected changes only

### Success Criteria
- 6/6 API docs have Configuration sections
- Migration guide created
- Release notes status updated
- All changes committed and pushed

---

## Files to Modify

### Step 1: Add Configuration Sections (6 files)
1. `docs/api/bsl-agent.md` - Add ## Configuration after ## Endpoints
2. `docs/api/captioning-agent.md` - Add ## Configuration after ## Endpoints
3. `docs/api/openclaw-orchestrator.md` - Add ## Configuration after ## Endpoints
4. `docs/api/operator-console.md` - Add ## Configuration after ## Endpoints
5. `docs/api/scenespeak-agent.md` - Add ## Configuration after ## Endpoints
6. `docs/api/sentiment-agent.md` - Add ## Configuration after ## Endpoints

### Step 2: Fix Version References (2 files)
1. `docs/release-notes/v0.5.0.md` - Update status to "planned"
2. `docs/migration/v0.3-to-v0.4.md` - Create new migration guide

---

## Definition of Done

- [ ] All 6 API docs have ## Configuration section
- [ ] Configuration sections include environment variables
- [ ] Configuration sections include default values
- [ ] Migration guide created (v0.3-to-v0.4.md)
- [ ] Release notes status updated (v0.5.0 → planned)
- [ ] All changes committed
- [ ] Changes pushed to GitHub
- [ ] Final verification passed

---

*Design Document - Project Chimera v0.4.0 - March 6, 2026*
