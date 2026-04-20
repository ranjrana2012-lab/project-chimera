# Services Status

**Last Updated**: April 10, 2026
**Total Services**: 11 deployed
**Health Status**: All services operational

---

## Service Inventory

### Core Services

#### 1. Nemoclaw Orchestrator
| Attribute | Value |
|-----------|-------|
| **Port** | 8000 |
| **Status** | ✅ Deployed |
| **Health** | http://localhost:8000/health |
| **Description** | Core orchestration and agent coordination |
| **Dependencies** | Redis, Kafka, SceneSpeak Agent |
| **Last Verified** | April 10, 2026 |
| **Tests** | 81 passing |

#### 2. SceneSpeak Agent
| Attribute | Value |
|-----------|-------|
| **Port** | 8001 |
| **Status** | ✅ Deployed |
| **Health** | http://localhost:8001/health |
| **Description** | Scene description and dialogue generation |
| **Dependencies** | Nemoclaw Orchestrator, GLM-4.7 API |
| **Last Verified** | April 10, 2026 |
| **Tests** | 80 passing |

#### 3. Sentiment Agent
| Attribute | Value |
|-----------|-------|
| **Port** | 8004 |
| **Status** | ✅ Deployed |
| **Health** | http://localhost:8004/health |
| **Description** | Sentiment analysis using BETTAfish and MIROFISH models |
| **Dependencies** | None (standalone ML service) |
| **ML Models** | BETTAfish (sentiment), MIROFISH (emotion) |
| **Last Verified** | April 10, 2026 |
| **Tests** | 82 passing |
| **Response Time** | <500ms target |

#### 4. Safety Filter
| Attribute | Value |
|-----------|-------|
| **Port** | 8006 |
| **Status** | ✅ Deployed |
| **Health** | http://localhost:8006/health |
| **Description** | Content moderation and safety filtering |
| **Dependencies** | None (standalone service) |
| **Last Verified** | April 10, 2026 |
| **Tests** | 25 passing |

#### 5. Operator Console
| Attribute | Value |
|-----------|-------|
| **Port** | 8007 |
| **Status** | ✅ Deployed |
| **Health** | http://localhost:8007/health |
| **Description** | Human oversight and control interface |
| **Dependencies** | All services (orchestrator) |
| **Last Verified** | April 10, 2026 |
| **Tests** | 40 passing |

---

### Infrastructure Services

#### 6. Dashboard
| Attribute | Value |
|-----------|-------|
| **Port** | 8013 |
| **Status** | ✅ Deployed |
| **Health** | http://localhost:8013/health |
| **Description** | Health monitoring UI and service dashboard |
| **Dependencies** | Health Aggregator |
| **Last Verified** | April 10, 2026 |
| **Tests** | 12 passing |

#### 7. Health Aggregator
| Attribute | Value |
|-----------|-------|
| **Port** | 8012 |
| **Status** | ✅ Deployed |
| **Health** | http://localhost:8012/health |
| **Description** | Service health polling and status aggregation |
| **Dependencies** | All services |
| **Last Verified** | April 10, 2026 |
| **Tests** | 18 passing |

---

### Supporting Services

#### 8. Echo Agent
| Attribute | Value |
|-----------|-------|
| **Port** | 8014 |
| **Status** | ✅ Deployed (Week 3 Complete) |
| **Health** | http://localhost:8014/health |
| **Description** | Simple input/output relay for testing |
| **Dependencies** | None (standalone) |
| **Last Verified** | April 10, 2026 |
| **Tests** | 15 passing |

#### 9. Translation Agent
| Attribute | Value |
|-----------|-------|
| **Port** | 8006 (shares with Safety Filter) |
| **Status** | ✅ Deployed (Week 4 Complete) |
| **Health** | http://localhost:8006/health |
| **Description** | Multi-language translation (15 languages supported) |
| **Dependencies** | BSL Avatar Service (for BSL translation) |
| **Languages** | English, Spanish, French, German, Italian, Portuguese, Dutch, Polish, Russian, Japanese, Chinese, Arabic, Hindi, BSL |
| **Last Verified** | April 10, 2026 |
| **Tests** | 31 passing |

#### 10. Music Generation
| Attribute | Value |
|-----------|-------|
| **Port** | 8011 |
| **Status** | ✅ Deployed |
| **Health** | http://localhost:8011/health |
| **Description** | Audio generation for performances |
| **Dependencies** | Sentiment Agent (for mood adaptation) |
| **Last Verified** | April 10, 2026 |
| **Tests** | 20 passing |

#### 11. Opinion Pipeline Agent
| Attribute | Value |
|-----------|-------|
| **Port** | 8020 |
| **Status** | ✅ Deployed |
| **Health** | http://localhost:8020/health |
| **Description** | Opinion processing and aggregation |
| **Dependencies** | Kafka, Nemoclaw Orchestrator |
| **Last Verified** | April 10, 2026 |
| **Tests** | 22 passing |

---

## Future Services (Phase 2)

### Planned Enhancements

#### Caption Agent
| Attribute | Planned Value |
|-----------|---------------|
| **Port** | TBD |
| **Status** | 📋 Planned |
| **Description** | Formats output as accessible captions |
| **Features** | SRT subtitle generation, high-contrast formatting |

#### Context Agent
| Attribute | Planned Value |
|-----------|---------------|
| **Port** | TBD |
| **Status** | 📋 Planned |
| **Description** | Maintains conversation state and context |
| **Features** | State management, Redis persistence |

#### Analytics Agent
| Attribute | Planned Value |
|-----------|---------------|
| **Port** | TBD |
| **Status** | 📋 Planned |
| **Description** | Tracks usage, performance, generates reports |
| **Features** | Logging pipeline, metrics collection |

---

## Infrastructure Components

| Component | Port | Status | Purpose |
|-----------|------|--------|---------|
| **Redis** | 6379 | ✅ Running | Caching and state management |
| **Kafka** | 9092 | ✅ Running | Event streaming |
| **Zookeeper** | 2181 | ✅ Running | Kafka coordination |
| **Milvus** | 19530 | ✅ Running | Vector database |
| **etcd** | 2379 | ✅ Running | Service discovery |
| **Minio** | 9000 | ✅ Running | S3-compatible storage |
| **Prometheus** | 9090 | ✅ Running | Metrics collection |
| **Jaeger** | 16686 | ✅ Running | Distributed tracing |
| **Grafana** | 3000 | ✅ Running | Monitoring dashboard |
| **Netdata** | 19999 | ✅ Running | System monitoring |

---

## Service Dependencies

```
nemoclaw-orchestrator (8000)
├── scenespeak-agent (8001)
├── sentiment-agent (8004)
│   └── BETTAfish/MIROFISH models
├── safety-filter (8006)
├── operator-console (8007)
├── translation-agent (8006)
│   └── bsl-avatar-service
├── music-generation (8011)
│   └── sentiment-agent (8004)
└── opinion-pipeline-agent (8020)
    ├── kafka
    └── nemoclaw-orchestrator

health-aggregator (8012)
├── all services (health polling)

dashboard (8013)
└── health-aggregator (8012)
```

---

## Health Check Summary

| Service | /health | /health/ready | /health/live | Notes |
|---------|---------|---------------|--------------|-------|
| nemoclaw-orchestrator | ✅ | ✅ | ✅ | All endpoints operational |
| scenespeak-agent | ✅ | ✅ | ✅ | All endpoints operational |
| sentiment-agent | ✅ | ✅ | ✅ | ML models loaded |
| safety-filter | ✅ | ✅ | ✅ | Content filters active |
| operator-console | ✅ | ✅ | ✅ | UI accessible |
| dashboard | ✅ | ✅ | ✅ | Data populated |
| health-aggregator | ✅ | ✅ | ✅ | Polling all services |
| echo-agent | ✅ | ✅ | ✅ | Simple relay working |
| translation-agent | ✅ | ✅ | ✅ | All languages available |
| music-generation | ✅ | ✅ | ✅ | Audio generation working |
| opinion-pipeline-agent | ✅ | ✅ | ✅ | Pipeline processing |

---

## Test Results by Service

| Service | Tests | Passing | Failing | Coverage |
|---------|-------|---------|---------|----------|
| nemoclaw-orchestrator | 81 | 81 | 0 | 78% |
| scenespeak-agent | 80 | 80 | 0 | 79% |
| sentiment-agent | 82 | 82 | 0 | 85% |
| safety-filter | 25 | 25 | 0 | 72% |
| operator-console | 40 | 40 | 0 | 75% |
| dashboard | 12 | 12 | 0 | 68% |
| health-aggregator | 18 | 18 | 0 | 70% |
| echo-agent | 15 | 15 | 0 | 82% |
| translation-agent | 31 | 31 | 0 | 80% |
| music-generation | 20 | 20 | 0 | 74% |
| opinion-pipeline-agent | 22 | 22 | 0 | 76% |
| shared modules | 168 | 168 | 0 | 81% |
| **Total** | **594** | **594** | **0** | **81%** |

---

## Deployment Commands

### Start All Services
```bash
docker-compose up -d
```

### Stop All Services
```bash
docker-compose down
```

### Restart Single Service
```bash
docker-compose restart nemoclaw-orchestrator
```

### View Service Logs
```bash
docker-compose logs -f nemoclaw-orchestrator
```

### Check Service Status
```bash
docker-compose ps
```

---

## Monitoring

### Grafana Dashboards
- **System Overview**: http://localhost:3000/d/system-overview
- **Service Health**: http://localhost:3000/d/service-health
- **Performance**: http://localhost:3000/d/performance

### Prometheus Metrics
- **Service Metrics**: http://localhost:9090/metrics
- **Service Health**: http://localhost:9090/api/v1/targets

### Jaeger Traces
- **Search Traces**: http://localhost:16686/search
- **Service Dependencies**: http://localhost:16686/dependencies

---

## Troubleshooting

### Service Not Starting
1. Check logs: `docker-compose logs <service>`
2. Check port conflicts: `lsof -i :<port>`
3. Check dependencies: `docker-compose ps`

### Health Check Failing
1. Check service logs for errors
2. Verify dependencies are running
3. Check environment variables in `.env`

### High Memory Usage
1. Check resource usage: `docker stats`
2. Adjust limits in `docker-compose.yml`
3. Scale down replicas if needed

---

**Last Updated**: April 10, 2026
**Next Update**: As new services are deployed
