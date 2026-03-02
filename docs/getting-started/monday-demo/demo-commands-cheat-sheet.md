# Demo Commands Cheat Sheet

**Print this before the 4pm demo!**

---

## Quick Health Checks

```bash
# All services health
for port in 8000 8001 8002 8003 8004 8005 8006 8007; do
    echo "Port $port:"
    curl -s http://localhost:$port/health/live | jq . || echo "Not responding"
done
```

---

## Service Endpoints to Demo

| Service | Port | Command | What It Shows |
|---------|------|---------|---------------|
| OpenClaw | 8000 | `curl http://localhost:8000/v1/skills` | List available skills |
| SceneSpeak | 8001 | `curl -X POST http://localhost:8001/v1/generate -H "Content-Type: application/json" -d '{"prompt":"Hello actor"}'` | Generate dialogue |
| Captioning | 8002 | `curl http://localhost:8002/docs` | API documentation |
| Operator Console | 8007 | Open browser to `http://localhost:8007` | Dashboard UI |

---

## Architecture Demo Commands

```bash
# Show project structure
tree -L 2 -I 'venv|__pycache__|.git'

# Show services directory
ls -la services/

# Show infrastructure
ls -la infrastructure/

# Show GitHub repository
gh repo view --web
```

---

## Git Workflow Demo

```bash
# Show current branch
git branch

# Show recent commits
git log --oneline -5

# Create feature branch (demo)
git checkout -b demo/student-introduction

# Show status
git status

# Switch back to master
git checkout master
```

---

## GitHub Project Board Demo

```bash
# Show project boards
gh project list

# View project
gh project view PVT_kwHODhT54s4BQjG4

# Show issues
gh issue list --label sprint-0

# Create a test issue (demo)
gh issue create --title "Demo: Test issue created during call" --body "This is a demo issue"
```

---

## Troubleshooting (If Something Goes Wrong)

```bash
# Restart k3s
sudo systemctl restart k3s

# Restart a specific service
cd services/<service-name>
source venv/bin/activate
python -m uvicorn main:app --port <port> --reload

# Kill stuck processes
pkill -f uvicorn
```

---

**Bring this printed sheet to the demo!**
