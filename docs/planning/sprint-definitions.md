# Sprint Definitions

**Version:** 1.0
**Last Updated:** March 2026
**For:** Project Chimera Development Team

---

## Overview

This document defines sprint structure, ceremonies, and workflow for Project Chimera development. Sprints are time-boxed iterations used to plan, execute, and deliver incremental value.

---

## Sprint Structure

### Sprint Duration

**Length:** 2 weeks (10 business days)
**Sprint Planning:** First day (Monday 9-11am)
**Sprint Review & Retrospective:** Last day (Friday 2-4pm)
**Team Velocity:** Measured in story points

### Sprint Timeline

```
Week 1:
┌─────────────────────────────────────────────────────────────┐
│ Mon │ Tue │ Wed │ Thu │ Fri │                             │
│─────┼─────┼─────┼─────┼─────├─────────────────────────────────┤
│Plan │Dev │Dev │Dev │Dev │    Development Focus          │
└─────┴─────┴─────┴─────┴─────┴─────────────────────────────────┘

Week 2:
┌─────────────────────────────────────────────────────────────┐
│ Mon │ Tue │ Wed │ Thu │ Fri │                             │
│─────┼─────┼─────┼─────┼─────├─────────────────────────────────┤
│ Dev │ Dev │ Dev │ Dev │Rev │    Development + Wrap-up       │
└─────┴─────┴─────┴─────┴─────┴─────────────────────────────────┘
```

---

## Sprint Ceremonies

### 1. Sprint Planning (Day 1, 9-11am)

**Purpose:** Plan work for the upcoming sprint

**Participants:** All team members, Scrum Master (if applicable)

**Agenda:**
1. Review sprint goal (1 min)
2. Review capacity (2 min)
3. Story estimation (30 min)
4. Story commitment (5 min)
5. Action items (2 min)

**Inputs:**
- Product backlog (prioritized items)
- Team velocity (from previous sprints)
- Team capacity (available hours)

**Outputs:**
- Sprint backlog (committed stories)
- Sprint goal statement
- Action items

**Sprint Goal Template:**
```markdown
As a [team], we want to [deliver value]
so that [customer/user benefit].
```

---

### 2. Daily Standup (Daily, 9:00-9:15am)

**Purpose:** Synchronize activities and plan for the next 24 hours

**Participants:** All team members

**Format:** Each person answers 3 questions:
1. What did I complete yesterday?
2. What will I work on today?
3. Do I have any blockers?

**Timeboxed:** 15 minutes max

**Example:**
```
Yesterday: Implemented dialogue caching for SceneSpeak Agent
Today: Writing unit tests for caching feature
Blockers: None - on track
```

---

### 3. Sprint Review (Last Day, 2-3pm)

**Purpose:** Review and demonstrate completed work

**Participants:** All team members, stakeholders welcome

**Format:** Demo of completed features

**Agenda:**
1. Review sprint goal (1 min)
2. Demo completed stories (30-45 min)
3. Collect feedback (5 min)
4. Celebrate wins! (5 min)

**Demo Format:**
- Show, don't tell (live demo preferred)
- 2-3 minutes per story
- Focus on working software

---

### 4. Sprint Retrospective (Last Day, 3-4pm)

**Purpose:** Inspect and adapt team process

**Participants:** Team members only (no stakeholders)

**Agenda:**
1. What went well? (5 min)
2. What could be improved? (5 min)
3. Action items for next sprint (5 min)

**Outputs:**
- Process improvements
- Action items with owners
- Updated Definition of Done

---

## Story Points

### Estimation Scale

| Points | Description | Example |
|--------|-------------|---------|
| 1 | Trivial fix, well-understood | Fix typo in config |
| 2 | Simple, low complexity | Add unit test |
| 3 | Moderate complexity | Add simple API endpoint |
| 5 | Complex, multiple components | Add caching layer |
| 8 | Very complex, unknowns | Integrate new service |
| 13 | Research spike | Explore new technology |

### Estimating Process

1. **Break down story** - Split large stories into smaller ones
2. **Discuss complexity** - Identify technical challenges
3. **Reference similar work** - Compare to past stories
4. **Reach consensus** - Team agrees on estimate
5. **Track velocity** - Compare estimates to actuals

### Velocity Calculation

```
Velocity = Sum of completed story points per sprint

Example:
Sprint 1: Completed 13 + 8 + 3 + 5 + 2 = 31 points
Sprint 2: Completed 21 + 5 + 3 + 8 + 2 = 39 points
Average Velocity: (31 + 39) / 2 = 35 points/sprint
```

### Capacity Planning

**Team Capacity:**
```
Available Hours = Team Size × Sprint Days × Hours per Day
Example: 6 people × 10 days × 6 hours = 360 hours

Story Points = Velocity (from previous sprints)
Example: 35 points

Buffer: Reserve 20% capacity for unplanned work
Available Points = Story Points × 0.8 = 28 points
```

---

## Definition of Done

A story is considered "done" when:

### Code Quality
- [ ] Code reviewed and approved
- [ ] Passes all automated checks (CI/CD)
- [ ] No known bugs
- [ ] Code formatted and linted

### Testing
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing (if applicable)
- [ ] Test coverage ≥80%
- [ ] Performance tested (if applicable)

### Documentation
- [ ] Docstrings on public functions
- [ ] API documentation updated (if API change)
- [ ] README updated (if user-facing change)
- [ ] Architecture doc updated (if architectural change)

### Deployment
- [ ] Deployed to staging environment
- [ ] Smoke tested on staging
- [ ] Deployment documented
- [ ] Monitoring/metrics configured

---

## Backlog Management

### Product Backlog

**Owner:** Product Owner / Technical Lead

**Maintenance:**
- Prioritize by value and risk
- Refine high-priority items before sprint planning
- Keep items sized appropriately (≤13 points)
- Remove obsolete items

### Sprint Backlog

**Created:** During sprint planning
**Frozen:** After sprint planning (no changes unless critical)

### Backlog Refinement

**When:** Weekly, between sprints
**Duration:** 1 hour
**Participants:** Product Owner, Technical Lead, key contributors

**Activities:**
- Review top 10 backlog items
- Break down large stories
- Estimate stories
- Acceptance criteria clarified

---

## Story States

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│  Backlog   │───▶│  Refining  │───▶│  Sprint     │───▶│  In Progress│
│            │    │            │    │  Backlog    │    │            │
└────────────┘    └────────────┘    └────────────┘    └────────────┘
                           │                            │
                           ▼                            ▼
                    ┌────────────┐    ┌────────────┐
                    │  Completed  │◀───│  Blocked    │
                    └────────────┘    └────────────┘
```

---

## Sprint Anti-Patterns

### 1. Overcommitting

**Problem:** Committing more work than team can deliver

**Signs:**
- Stories carry over every sprint
- Velocity consistently lower than committed
- Team consistently works overtime

**Solution:** Use historical velocity, reserve buffer for uncertainty

### 2. Mid-Sprint Changes

**Problem:** Changing sprint backlog mid-sprint

**Signs:**
- New stories added during sprint
- Stories swapped out mid-sprint
- Sprint goal changes

**Solution:** Protect sprint backlog, defer new stories to next sprint

### 3. Unclear Requirements

**Problem:** Stories lack clear acceptance criteria

**Signs:**
- Ambiguous acceptance criteria
- Multiple interpretations possible
- Requires clarification during sprint

**Solution:** Refine stories before sprint planning

### 4. Missing Definition of Done

**Problem:** Stories marked "done" but incomplete

**Signs:**
- Missing tests
- No documentation
- Not deployed

**Solution:** Enforce Definition of Done checklist

---

## Metrics & Reporting

### Sprint Metrics

Track these metrics each sprint:

**Velocity:**
- Committed story points
- Completed story points
- Carryover story points
- Commit rate (completed/committed)

**Quality:**
- Defect escape rate (bugs found after sprint)
- Test coverage percentage
- CI/CD pass rate

**Process:**
- Stories added mid-sprint (should be 0)
- Stories removed mid-sprint (should be 0)
- Sprint backlog changes

### Sprint Report Template

```markdown
# Sprint X Report

**Dates:** [Start Date] - [End Date]
**Sprint Goal:** [Goal statement]

## Summary

- **Committed:** X story points
- **Completed:** Y story points
- **Carryover:** Z story points
- **Commit Rate:** Y/X (Y%)

## Completed Stories

- [Story 1] - Description and outcome
- [Story 2] - Description and outcome
- ...

## Metrics

- **Defect Escape:** X bugs found post-sprint
- **Test Coverage:** Y%
- **CI/CD Pass Rate:** Z%

## Process Improvements

- [Improvement 1] - What we're doing differently next sprint
- [Improvement 2] - Process changes implemented

## Next Sprint

- **Proposed Start Date:** [Date]
- **Team Capacity:** [Available hours]
- **Proposed Velocity:** [Story points]
```

---

## Roles & Responsibilities

### Product Owner / Technical Lead

- Maintain product backlog
- Prioritize stories
- Accept completed work
- Define sprint goal

### Scrum Master (if applicable)

- Facilitate ceremonies
- Remove blockers
- Protect sprint scope
- Track sprint metrics

### Team Members

- Complete assigned stories
- Update task status daily
- Participate in ceremonies
- Raise blockers early

---

## Related Documentation

- [Development Guide](../DEVELOPMENT.md) - Development workflow
- [Evaluation Criteria](../contributing/evaluation-criteria.md) - Review criteria
- [Contributing Guide](../CONTRIBUTING.md) - Contribution process

---

*Sprint Definitions - Project Chimera v0.4.0 - March 2026*
