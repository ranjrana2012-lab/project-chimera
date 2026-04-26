# Project Chimera Guides

Start here if you are browsing documentation directly.

## Current Setup Guides

- `GETTING_STARTED.md` - canonical overview for the current repository.
- `QUICK_START.md` - shortest route selector and quick commands.
- `STUDENT_LAPTOP_SETUP.md` - default student/laptop setup path.
- `Student_Quick_Start.md` - classroom-friendly quick start with student focus areas.
- `DGX_SPARK_SETUP.md` - NVIDIA DGX Spark / GB10 ARM64 setup path.
- `DOCKER.md` - current Docker Compose guide.
- `TESTING.md` - validated test commands.
- `DEPLOYMENT.md` - local, Docker, and DGX deployment notes.
- `DEVELOPMENT.md` - development workflow.

## Route Selection

Agents should read the root `AGENTS.md` first. Humans can run:

```bash
python scripts/detect_runtime_profile.py
```

Default to `STUDENT_LAPTOP_SETUP.md` unless the machine is clearly a DGX Spark /
GB10 ARM64 host with NVIDIA Container Runtime.

## Historical or Specialized Guides

Some guides in this folder describe older research, simulation, grant, or
operator-console details. Treat the current setup guides above as authoritative
for installation and validation.
