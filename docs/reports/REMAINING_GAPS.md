# Remaining Gaps

No blocking gaps remain for the supported local operator-console, student Docker, MVP/DGX, or Kimi host-facing routes validated on this machine.

## Non-blocking Gaps

| Gap | Why it remains | Required to close | Operational risk |
| --- | --- | --- | --- |
| Protobuf generated-code compatibility is provisional | Operator/test env is constrained to protobuf 4.25.9 by opentelemetry-proto<5, while Kimi tooling uses protobuf 6.33.6/protoc 31.1. Regenerating now would reintroduce a protobuf 6 runtime guard. | Choose one protobuf generation/runtime strategy and regenerate with pinned tooling that all envs can import. | Medium: careless upgrades can break OpenTelemetry or Kimi imports. |
| Skipped extended-stack tests in maintainer validation | Skips are external secrets, unsupported extended-stack services, planned endpoints, Docker-DNS-only checks, or known model limitations. | Provide real credentials, validate the relevant extended stack, and update legacy tests to the active route. | Medium/high if it requires adding services or secrets. |
| 4 warnings in final full suite | Third-party/future warnings from protobuf Python 3.14 compatibility, Starlette/python-multipart, and OpenTelemetry/pkg_resources. | Upgrade/pin dependencies once upstream compatibility is settled. | Low for current Python 3.12 runtime. |
| Legacy top-level host-local integration group is not part of final pass | Forced host-local execution still includes unsupported extended services and legacy endpoint expectations. | Split legacy extended-stack tests behind a marker or update them to the MVP route. | Medium: broad test rewrites could mask actual future-service requirements. |
| External APIs are not validated | No GLM_API_KEY or Google Translate API configuration was fabricated. | Provide real secrets/endpoints in a safe local env and rerun external integration tests. | Medium: uses paid/external services and secrets. |
| OTLP collector is not configured | Containers log localhost:4317 exporter failures, but health/tests pass. | Add a collector to Compose or disable OTLP export for local validation. | Low: observability noise only in this run. |
| Kimi/OpenClaw response quality is tuned for validation latency | Token budgets are deliberately conservative to keep local tests stable on this host. | Tune prompts, stop sequences, and max token budgets for production dialogue quality. | Low/medium: higher quality may increase latency and test budgets. |
| Host has no python command | Ubuntu host only provides python3. Repo commands were corrected; no machine-local symlink was added. | Install python-is-python3 or add a local alias if desired. | Low: repo no longer requires host python for validated routes. |
