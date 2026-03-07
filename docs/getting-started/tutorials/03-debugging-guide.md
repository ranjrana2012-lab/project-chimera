# Debugging Guide Tutorial

**Type:** Video Script / Screencast Tutorial
**Duration:** 15-20 minutes
**Target Audience:** Students needing to troubleshoot issues
**Prerequisites:** Environment setup complete

---

## Script Outline

### Part 1: Introduction (0:00-1:00)

**Visual:** Title card - "Debugging Project Chimera"

**Speaker:** "Every developer encounters bugs. This tutorial teaches you how to debug Project Chimera services effectively using tools and techniques."

---

### Part 2: Common Issues and Solutions (1:00-5:00)

**Speaker:** "Let's cover common issues you might face:"

#### Issue 1: Service Not Starting

**Visual:** Terminal showing failed pod

```bash
$ kubectl get pods -n live
NAME                           READY   STATUS              RESTARTS   AGE
scenespeak-agent-xxx-yyy        0/1     CrashLoopBackOff   5          2m
```

**Speaker:** "Debug steps:"

```bash
# Check pod logs
kubectl logs scenespeak-agent-xxx-yyy -n live

# Check previous logs if container restarted
kubectl logs scenespeak-agent-xxx-yyy -n live --previous

# Describe pod for events
kubectl describe pod scenespeak-agent-xxx-yyy -n live
```

**Speaker:** "Common causes:
- Missing dependencies (pip install missing packages)
- Wrong environment variables
- Port already in use
- Missing model files"

#### Issue 2: High Memory/CPU Usage

```bash
# Check resource usage
kubectl top pods -n live
kubectl top nodes
```

**Speaker:** "Solutions:
- Reduce batch size
- Add memory limit to deployment
- Scale up replicas"

#### Issue 3: Service Not Responding

```bash
# Port forward to local
kubectl port-forward svc/scenespeak-agent 8001:8001 -n live

# Test locally
curl http://localhost:8001/health
```

---

### Part 3: Local Debugging with pdb (5:00-9:00)

**Speaker:** "Use Python's built-in debugger:"

**Visual:** VS Code with Python file

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb if installed
import ipdb; ipdb.set_trace()
```

**Speaker:** "Debugging commands:
- `n` - Next line
- `s` - Step into function
- `c` - Continue
- `p variable` - Print variable
- `l` - List code
- `q` - Quit debugger"

**Visual:** VS Code debug configuration

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "services/scenespeak/main:app",
        "--host", "localhost",
        "--port", "8001",
        "--reload"
      ]
    }
  ]
}
```

**Speaker:** "With VS Code debugging:
- Set breakpoints by clicking line numbers
- Inspect variables in the Debug panel
- Step through code with F10/F11
- Watch expressions
- Debug console for evaluating code"

---

### Part 4: Kubernetes Debugging (9:00-13:00)

#### Pod Exec

**Speaker:** "Exec into a running pod:"

```bash
# Exec into container
kubectl exec -it scenespeak-agent-xxx-yyy -n live -- /bin/bash

# Inside container
ls -la
ps aux
env | grep -i python
```

#### Logs and Events

```bash
# Follow logs in real-time
kubectl logs scenespeak-agent-xxx-yyy -n live --follow

# Check all pods' logs
kubectl logs -l app=scenespeak-agent -n live --tail=50

# Check events
kubectl get events -n live --sort-by='.lastTimestamp'
```

#### Network Debugging

```bash
# Test service connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- wget -O- http://scenespeak-agent:8001/health

# DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup scenespeak-agent

# Port connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- nc -zv scenespeak-agent 8001
```

---

### Part 5: Performance Debugging (13:00-16:00)

**Speaker:** "Debug performance issues:"

#### Profiling

```python
# Add profiling to your code
import cProfile
import pstats

def my_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # Your code here
    result = slow_operation()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats(10)  # Top 10 functions
```

#### Memory Profiling

```bash
# Memory profiler
pip install memory_profiler

# In code
from memory_profiler import profile

@profile
def my_function():
    # Your code
    pass
```

#### Tracing

**Speaker:** "Use distributed tracing:"

```bash
# Access Jaeger UI
open http://localhost:16686

# Search for your trace ID
# View span timeline
# Find slow operations
```

---

### Part 6: Debugging Checklist (16:00-18:00)

**Visual:** Debugging checklist

**Speaker:** "When debugging, follow this checklist:

1. **Define the problem** - What exactly is failing?
2. **Reproduce the issue** - Can you make it fail consistently?
3. **Check logs** - What do the logs say?
4. **Isolate the cause** - Which component is failing?
5. **Fix and verify** - Does your fix solve it?
6. **Add tests** - Prevent regression"

---

### Part 7: Getting Help (18:00-20:00)

**Speaker:** "Still stuck? Get help:

1. **Check existing issues** - Someone might have solved it
2. **Search the codebase** - Find similar working code
3. **Read the docs** - Troubleshooting guides exist
4. **Ask in Slack** - #project-chimera-students
5. **Office hours** - Monday-Friday 2-4pm
6. **Create an issue** - Include logs, error messages, steps to reproduce"

**Speaker:** "When asking for help, include:
- What you're trying to do
- What you expected to happen
- What actually happened
- Error messages and logs
- Steps you've already tried"

---

## Quick Reference

### Common Debugging Commands

```bash
# Check pod status
kubectl get pods -n live

# View logs
kubectl logs <pod-name> -n live --follow

# Exec into pod
kubectl exec -it <pod-name> -n live -- /bin/bash

# Port forward
kubectl port-forward svc/<service> <local-port>:<service-port> -n live

# Describe pod
kubectl describe pod <pod-name> -n live

# Check events
kubectl get events -n live

# Check resource usage
kubectl top pods -n live
kubectl top nodes
```

### Python Debugging

```python
# Set breakpoint
import pdb; pdb.set_trace()

# VS Code debugger
# Set breakpoints and use F5/F10/F11
```

### Tracing

```bash
# View traces in Jaeger
open http://localhost:16686

# Analyze trace
python scripts/analyze-trace.py <trace-id>
```

---

## Related Resources

- [Troubleshooting Runbook](../../demo/troubleshooting.md)
- [Performance Analysis Runbook](../../runbooks/performance-analysis.md)
- [Distributed Tracing Runbook](../../runbooks/distributed-tracing.md)
- [Development Guide](../../DEVELOPMENT.md) - Debugging section

---

**Next Tutorial:** See [API Documentation](../../reference/api.md) - Learn how to use service APIs.

---

*Debugging Guide Tutorial - Project Chimera v0.4.0 - March 2026*
