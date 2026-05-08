# Run Log Instructions

Status: HUMAN ACTION REQUIRED.

Run logs must come from actual commands. Do not write manual logs that pretend a
command was executed.

## Recommended Commands

```bash
python3 scripts/check_environment.py
python3 services/operator-console/chimera_core.py demo
python3 scripts/run_phase1_demo.py
python3 test_chimera_smoke.py
python3 scripts/privacy_preflight.py
```

## What A Useful Log Should Include

- Timestamp.
- Command run.
- Python version.
- Hardware note, if available.
- Input text.
- Sentiment or fallback route.
- Selected adaptive strategy.
- Generated response.
- Latency, if reported.

## Evidence Boundary

Generated logs should be stored privately for submission. Public git should only
contain scripts, instructions, and placeholders.
