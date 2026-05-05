# Operator Console API

Phase 1 exposes a small local API when the operator-console web route is
running.

Start it from `services/operator-console`:

```bash
PORT=18080 ./venv/bin/python chimera_web.py
```

Public demo endpoints:

- `GET /` - local dashboard.
- `GET /api/state` - current demo state.
- `POST /api/process` - process audience-style text.
- `GET /projection` - projection view.
- `GET /api/export` - export local session data.

Generated exports, logs, screenshots, and recordings are evidence artifacts.
Keep real evidence private and run `scripts/privacy_preflight.py` before
publishing.
