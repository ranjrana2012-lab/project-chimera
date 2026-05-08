# Project Chimera Phase 1 Case Study

## Summary

Project Chimera Phase 1 explored a local adaptive AI workflow for theatre R&D.
The public repository demonstrates a narrow technical foundation: audience-style
text is routed through sentiment analysis, mapped to an adaptive response
strategy, and exposed through a CLI and lightweight local web route.

## Problem Explored

The R&D question was whether a theatre-facing AI system could adapt its response
style based on emotional tone while remaining simple enough to run locally for
review and iteration.

## What Was Built

The Phase 1 repository includes:

- a CLI demonstrator in `services/operator-console/chimera_core.py`;
- a local web route in `services/operator-console/chimera_web.py`;
- smoke tests and public-cleanup contract tests;
- setup and demo documentation;
- public/private evidence boundary checks.

The demonstrated strategies are:

- `momentum_build` for positive inputs;
- `supportive_care` for negative inputs;
- `grounding_support` for confused or overwhelmed inputs;
- `reflective_transition` for intense but inspiring inputs;
- `standard_response` for neutral inputs.

## What Was Not Claimed

Phase 1 does not claim:

- a completed public performance;
- a livestream or public audience workflow;
- formal accessibility testing;
- BSL/avatar delivery;
- testimonials or measured audience impact;
- a full student programme;
- a complete public evidence pack.

## Reviewer Replication

Use `docs/closeout/REPLICATION_TOOLKIT.md` or `QUICKSTART.md` to run the local
demo and smoke checks. Generated screenshots, recordings, and logs should be
stored privately if used as grant evidence.

## Close-Out Use

This case study can support a final narrative about a Phase 1 technical
demonstrator. It should be paired with private evidence for recordings,
screenshots, spending records, meeting notes, and any owner-provided final
submission material.
