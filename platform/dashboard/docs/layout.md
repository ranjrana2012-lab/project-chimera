# Dashboard Layout Design Document

**Version:** 1.0.0
**Date:** 2026-03-04
**Author:** Project Chimera Team

---

## Overview

The Dashboard Service provides a web-based UI for monitoring test execution, coverage trends, and system health across all Project Chimera services.

---

## Layout Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                     HEADER                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │ Project       │  │ Test Run ID   │  │ Last Updated │  │ Status       │                │
│  │ Chimera       │  │ run-abc123    │  │ 2m ago       │  │ ● Healthy    │                │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                     SUMMARY                                          │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌──────────────────────┐  │
│  │ Total Tests:          │  │ Coverage:             │  │ Success Rate:         │  │
│  │      2,547             │  │     82.5%             │  │       94.2%           │  │
│  │ ✅ 2,401 passed        │  │  ▲ 2.1% vs last      │  │  ▲ 1.5% vs last      │  │
│  │ ❌ 146 failed         │  │                       │  │                       │  │
│  └───────────────────────┘  └───────────────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SERVICE HEALTH STATUS                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │SceneSpeak  │  │ Captioning │  │    BSL     │  │  Sentiment  │  │  Safety     │  │
│  │   Agent    │  │   Agent    │  │   Agent    │  │   Agent    │  │  Filter     │  │
│  │  ● UP      │  │  ● UP      │  │  ● UP      │  │  ● UP      │  │  ● UP      │  │
│  │  2s ago    │  │  5s ago    │  │  3s ago    │  │  1s ago    │  │  8s ago    │  │
│  │  45/50     │  │ 120/125    │  │ 38/40     │  │ 15/15      │  │ 98/98      │  │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                                   │
│  │ Lighting   │  │   OpenClaw  │  │   Operator │                                   │
│  │   Service  │  │Orchestrator│  │   Console  │                                   │
│  │  ● UP      │  │  ● UP      │  │  ● UP      │                                   │
│  │  10s ago   │  │  1s ago    │  │  5s ago    │                                   │
│  │  15/15     │  │  189/203   │  │  5/5       │                                   │
│  └────────────┘  └────────────┘  └────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             TEST RESULTS TREND                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐   │
│  │  Pass Rate Over Time (Last 30 Runs)                                   │   │
│  │  100% ████████████████████████████████████████████████████████████████   │   │
│  │   95% ████████████████████████████████████████████████████████████████   │   │
│  │   90% ████████████████████████████████████████████████████████████████     │   │
│  │   85% ████████████████████████████████████████████████████████████        │   │
│  │   80% ██████████████████████████████████████████████████████             │   │
│  │                                        ┌─────────────────────────────────┐   │   │
│  │                                        │  25 runs: avg 92.3% pass rate    │   │   │
│  │                                        └─────────────────────────────────┘   │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────────────────┐   │
│  │  Service Pass Rates                                                    │   │
│  │  SceneSpeak  ████████████████████████  95.2%                       │   │
│  │  Captioning  ████████████████████████  94.5%                       │   │
│  │  BSL        █████████████████████████  97.8%                       │   │
│  │  Sentiment   ████████████████████████  88.3%                       │   │
│  │  Lighting   █████████████████████████  100.0%                      │   │
│  │  OpenClaw   ██████████████████████████  93.1%                       │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            COVERAGE METRICS                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐   │
│  │  Overall Coverage: 82.5% (4,231 / 5,127 lines)                                 │   │
│  │  [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]   82.5%   │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────────────────┐   │
│  │  Service Coverage Breakdown                                                │   │
│  │  Service          Coverage   Lines      Missing Files                │   │
│  │  ├─ SceneSpeak     88.3%     1,234      3       3 missing >80%   │   │
│  │  ├─ Captioning     78.1%     890        195                           │   │
│  │  ├─ BSL            92.5%     567        42                           │   │
│  │  ├─ Sentiment      85.2%     423        62                           │   │
│  │  ├─ Lighting       100.0%    150        0                            │   │
│  │  └─ OpenClaw       86.1%     1,867      259                          │   │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RECENT TEST RUNS                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐   │
│  │  Run ID         Status    Total    Passed   Failed   Duration   Timestamp     │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │  run-xyz123    ✅       547      523      24       2m 15s      5m ago        │   │
│  │  run-abc456    ✅       547      540       7        1m 58s      12m ago       │   │
│  │  run-def789    ✅       547      535      12       3m 22s      25m ago       │   │
│  │  run-ghi012    ❌       547      501      46       4m 10s      38m ago       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ALERTS & INCIDENTS                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐   │
│  │  ├─ ⚠️  SceneSpeak Agent high latency (>5s)                                    │   │
│  │  ├─ ⚠️  Coverage drop in BSL Agent (<80%)                                      │   │
│  ├─ ━️  3 flaky tests detected in Sentiment Agent                            │   │
│  │  └─ ℹ️  OpenClaw Orchestrator restarted                                        │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CI/CD PIPELINE STATUS                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐   │
│  │  Pipeline    Branch     Status      Commit     Duration                   │   │
│  ├───────────────────────────────────────────────────────────────────────┤   │
│  │  #4527      main       ✅         8d3e2f1    5m 23s                     │   │
│  │  #4526      main       ✅         1a9b5c3    4m 12s                     │   │
│  │  #4525      main       ✅         7f8d4e1    6m 45s                     │   │
│  │  #4524      main       ❌         2e3f5a9    2m 10s                     │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Color Scheme

| Status | Color | Usage |
|--------|------|-------|
| Success | Green | ✅, UP, high pass rates |
| Error | Red | ❌, DOWN, failures |
| Warning | Yellow | ⚠️, degraded performance |
| Info | Blue | ℹ️, informational |
| Neutral | Gray | Pending, unknown |

---

## Responsive Design

### Desktop (1440px+)
- 3-column layout for health, trends, coverage
- Full detail view
- Side navigation

### Tablet (768px - 1439px)
- 2-column layout
- Simplified health view
- Stacked panels

### Mobile (<768px)
- Single column layout
- Card-based UI
- Hamburger menu
- Pull-to-refresh

---

## Component Details

### Service Health Card
- **Service Name** with icon
- **Status Indicator**: 🟢 Up, 🔴 Down, 🟡 Degraded
- **Last Check**: "Xs ago"
- **Test Summary**: "Passed/Total"

### Test Results Chart
- **Line Chart**: Pass rate over time
- **Bar Chart**: Service-by-service comparison
- **Sparklines**: Mini trend indicators

### Coverage Progress
- **Overall Gauge**: Big progress bar
- **Service Breakdown**: Bar chart per service
- **Missing Files List**: Expandable details

### Alerts Panel
- **Severity Levels**: Info, Warning, Error, Critical
- **Auto-dismiss**: Info alerts dismiss after 30s
- **Acknowledge**: Manual dismiss for important alerts

---

## Data Refresh Strategy

| Component | Refresh Rate | Method |
|-----------|--------------|--------|
| Health Status | Every 10s | WebSocket subscription |
| Test Results | Every 30s | Polling API |
| Coverage Metrics | Every 5m | Polling API |
| CI/CD Status | Every 2m | Polling API |
| Alerts | Real-time | WebSocket |

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Frontend Framework | React (via existing dashboard) |
| HTTP Client | Fetch API / Axios |
| WebSocket | Native WebSocket API |
| Charts | Chart.js or Recharts |
| State Management | React Query / SWR |
| Styling | CSS Modules / Tailwind |
| Build | Vite (existing) |

---

**Status:** ✅ Design Complete
**Next Step:** Implement service health display (Task 3.2.2)
