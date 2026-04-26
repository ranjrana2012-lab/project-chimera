# Quick Start

This lowercase alias is kept for older links. The current validated setup route
is documented in:

- `docs/guides/QUICK_START.md`
- `docs/guides/STUDENT_LAPTOP_SETUP.md`
- `docs/guides/DGX_SPARK_SETUP.md`

For most users, start with the student/laptop route:

```powershell
cd services/operator-console
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe chimera_core.py demo
```

For agents, read `AGENTS.md` first.
