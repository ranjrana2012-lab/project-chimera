# Phase 1 Demo Troubleshooting

This page covers the public Phase 1 demo route only. Use the Student / Laptop
path unless a separate maintainer has explicitly chosen an advanced hardware
route.

## Quick Checks

Run these from the repository root:

```bash
services/operator-console/venv/bin/python verify_prerequisites.py
services/operator-console/venv/bin/python test_chimera_smoke.py
services/operator-console/venv/bin/python scripts/privacy_preflight.py
```

## CLI Demo Does Not Run

Check that the operator-console environment exists and dependencies are
installed:

```bash
cd services/operator-console
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python chimera_core.py demo
```

Expected result: the command prints the Phase 1 demo banner, runs the sample
sentiment/adaptation flow, and exits without requiring external API keys.

## Web Console Does Not Start

Start the web route from `services/operator-console`:

```bash
PORT=18080 ./venv/bin/python chimera_web.py
```

Open `http://127.0.0.1:18080`. If the page does not load, check whether the
port is already in use:

```bash
ss -ltnp | grep 18080
```

Choose another port if needed:

```bash
PORT=18081 ./venv/bin/python chimera_web.py
```

## API State Check Fails

With the web console running, verify the state endpoint:

```bash
curl -fsS http://127.0.0.1:18080/api/state
```

If this fails, restart the web process and rerun the command from the same
checkout. Keep logs under `internal/` if they contain local paths, timestamps,
or private evidence notes.

## Export Check Fails

With the web console running, verify export output:

```bash
curl -fsS http://127.0.0.1:18080/api/export
```

Generated exports are local evidence. Store real screenshots, recordings, logs,
receipts, invoices, and grant notes privately. Do not add them to public git.

## Privacy Preflight Fails

Run:

```bash
./services/operator-console/venv/bin/python scripts/privacy_preflight.py
```

Treat failures as blockers before publishing. Common causes are local `.env`
files, generated recordings, receipt or invoice paths, private grant material,
student/contact data, or token-looking strings.

## Demo Recording Problems

Use `scripts/capture_phase1_evidence.py` only for local evidence capture. The
public repository should contain placeholders under `evidence/`, not real
recordings or logs.

## Escalation Notes

When asking for help, include:

- the exact command that failed;
- the Python version from `python3 --version`;
- whether the CLI demo, web route, or privacy preflight failed;
- redacted logs with private paths, tokens, names, and grant details removed.
