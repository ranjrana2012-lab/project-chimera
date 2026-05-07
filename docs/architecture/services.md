# Services

Current public Phase 1 service maturity labels:

| Label | Surface | Current status |
| --- | --- | --- |
| `phase1-supported` | `services/operator-console/chimera_core.py` | CLI demonstrator and adaptive response logic. |
| `phase1-supported` | `services/operator-console/chimera_web.py` | Local web dashboard and demo API. |
| `phase1-supported` | `scripts/privacy_preflight.py` | Public/private safety gate before publishing. |
| `phase1-supported` | `scripts/capture_phase1_evidence.py` | Local evidence capture helper. |
| `experimental` | `services/openclaw-orchestrator/` | Multi-service orchestration research surface. Validate locally before presenting as current behavior. |
| `experimental` | `services/safety-filter/` | Service-level moderation research surface. Validate and harden before network exposure. |
| `advanced` | DGX Spark, Kimi, and GPU-backed compose routes | Hardware-specific routes that require matching local evidence. |
| `legacy` | Older service-topology docs and broad workflow files | Retained only where needed as compatibility pointers or manual owner-review workflows. |
| `experimental` | `services/zai-auth-proxy/` | Local-only token proxy experiment. Keep token files private and never expose it on a public interface. |

Other service directories are experimental or advanced routes unless their
specific guide says otherwise. Compose files, production-shaped workflow names,
and service directories are not production readiness evidence. Do not describe
them as public production behaviour without fresh validation evidence.
