# Phase 1 Demo Script

Use this script for a short public-safe walkthrough of the local adaptive AI
foundation. Keep claims narrow: Phase 1 demonstrates local CLI/web behavior, not
a finished theatre production or complete accessibility platform.

## 1. Introduce The Scope

Project Chimera Phase 1 accepts audience-style text, detects emotional tone,
routes the input to an adaptive response strategy, and exposes CLI/web outputs
for review.

Say explicitly:

- Student / Laptop is the default validation route.
- DGX Spark / GB10 and Kimi are advanced routes only when host evidence supports
  them.
- Private evidence, generated media, receipts, invoices, participant data, and
  `.env` files are not public repository material.

## 2. Run The Local CLI Demo

```bash
cd services/operator-console
./venv/bin/python chimera_core.py demo
```

Point out the expected behavior:

- positive text routes to `momentum_build`;
- negative text routes to `supportive_care`;
- confused or overwhelmed text routes to `grounding_support`;
- intense but inspiring text routes to `reflective_transition`;
- neutral text routes to `standard_response`.

## 3. Show Comparison Output

```bash
./venv/bin/python chimera_core.py compare "The audience is unsure but curious."
```

Explain that comparison mode is a local demonstrator for baseline-versus-adaptive
response behavior.

## 4. Show Caption And Export Behavior

```bash
./venv/bin/python chimera_core.py caption "Welcome to Project Chimera."
./venv/bin/python chimera_core.py export
```

Confirm the output files are generated locally and should not be committed if
they contain private run evidence.

## 5. Start The Web Route

```bash
PORT=18080 ./venv/bin/python chimera_web.py
```

Open `http://127.0.0.1:18080` and show:

- current state;
- processing an input;
- CSV export.

## 6. Close With Validation

From the repository root, run:

```bash
./services/operator-console/venv/bin/python verify_prerequisites.py
./services/operator-console/venv/bin/python test_chimera_smoke.py
./services/operator-console/venv/bin/python scripts/privacy_preflight.py
```

Do not claim DGX/Kimi validation unless those commands were run on matching
hardware with the required local credentials and model access.
