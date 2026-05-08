# Patch Summary

## Summary

This patch turns the prior "mostly working" state into a locally validated setup on the DGX/GB10 aarch64 host. The main themes are Kimi host publication, DGX runtime detection, Python 3 host compatibility, Kimi/protobuf import compatibility, SceneSpeak/OpenClaw live local LLM routing, Redis-backed OpenClaw caching, stronger test discovery, and clearer validation reports.

Close-out scope note: this is an engineering patch summary, not a complete grant
evidence pack. Do not use it to claim a public show, livestream, formal
accessibility testing, BSL/avatar delivery, testimonials, audience impact,
spending reconciliation, or final payment readiness.

## Files Changed

| File | Why it changed | Type | Follow-up |
| --- | --- | --- | --- |
| AGENTS.md | DGX route command now uses python3 and Docker GPU support wording covers CDI. | Permanent | None |
| Makefile | Repo-native targets avoid host python assumptions. | Permanent | None |
| QUICKSTART.md | Linux/macOS commands use venv Python/python3. | Permanent | None |
| README.md | Updated dashboard/DGX wording for python3 and Docker GPU support. | Permanent | None |
| docker-compose.dgx-spark.yml | Publishes Kimi HTTP/gRPC host ports, extends vLLM health startup window, sets safe Kimi runtime budgets. | Compatibility-focused | Tune token budgets for production quality |
| docs/guides/DGX_SPARK_SETUP.md | Aligns DGX setup commands with python3/CDI Docker GPU support. | Permanent | None |
| docs/guides/DEPLOYMENT.md | Aligns deployment commands with python3 and explicit venv usage. | Permanent | None |
| docs/guides/DEVELOPMENT.md | Aligns developer validation commands with explicit venv usage. | Permanent | None |
| docs/guides/DOCKER.md | Clarifies Docker GPU/CDI wording for DGX hosts. | Permanent | None |
| docs/guides/GETTING_STARTED.md | Updates first-run commands, ports, and python3/venv assumptions. | Permanent | None |
| docs/guides/KIMI_QUICKSTART.md | Documents host-facing Kimi validation against localhost ports and /model. | Permanent | None |
| docs/guides/QUICK_START.md | Updates route wording and validation guidance. | Permanent | None |
| docs/guides/README.md | Updates route-selection wording for Docker GPU/CDI support. | Permanent | None |
| docs/guides/STUDENT_GUIDE.md | Updates student Linux commands to python3 and venv-local execution. | Permanent | None |
| docs/guides/STUDENT_LAPTOP_SETUP.md | Fixes smoke-test path and current validation date. | Permanent | None |
| docs/guides/Student_Quick_Start.md | Updates student quick start commands and smoke-test path. | Permanent | None |
| docs/guides/TESTING.md | Updates local validation commands to explicit venv execution. | Permanent | None |
| pytest.ini | Limits active collection paths and registers performance/slow markers. | Permanent | Revisit if archived future_concepts should be restored |
| requirements-dev.txt | Adds prometheus-api-client for dashboard tests. | Permanent | None |
| scripts/detect_runtime_profile.py | Detects Docker GPU support even without nvidia runtime and reports dgx-spark high confidence. | Permanent | Add tests for CDI-only hosts |
| scripts/run-tests.sh | Defaults to python3 when PYTHON is unset. | Permanent | None |
| scripts/setup-monitoring.sh | Uses python3 in printed startup guidance. | Permanent | None |
| services/dashboard/main.py | Handles monitoring dependency paths/imports used by tests. | Permanent | None |
| services/kimi-super-agent/agent_coordinator.py | Adds async-compatible client coordination helpers expected by tests. | Compatibility-focused | Consolidate Kimi client abstractions later |
| services/kimi-super-agent/capability_detector.py | Supports test/runtime constructor options, protobuf/dict content, and additional capability hints. | Compatibility-focused | None |
| services/kimi-super-agent/kimi_client.py | Supports configurable model/endpoint/timeouts and safer payload handling. | Compatibility-focused | Tune timeout defaults if model changes |
| services/kimi-super-agent/kimi_orchestrator.py | Stabilizes startup/shutdown, signal handling, model defaults, and Kimi request budgets. | Compatibility-focused | None |
| services/kimi-super-agent/proto/kimi_pb2.py | Removes protobuf 6 runtime guard to allow protobuf 4 operator env imports. | Provisional | Regenerate/pin protobuf cleanly across envs |
| services/kimi_super_agent/__init__.py | Adds import compatibility package for hyphenated services/kimi-super-agent directory. | Compatibility-focused | Replace with real package rename in a major refactor |
| services/openclaw-orchestrator/main.py | Uses smaller local LLM default token budget, longer timeout, and per-key in-flight orchestration lock. | Permanent | Tune response quality/performance budget |
| services/operator-console/chimera_core.py | Keeps local CLI/web stable on this host and avoids shutdown/runtime warning path. | Permanent | Review Transformers generation warnings |
| services/safety-filter/models.py | Suppresses Pydantic protected namespace warning for model_* fields. | Permanent | None |
| services/scenespeak-agent/glm_client.py | Hardens fallback/client behavior when external GLM secrets are absent. | Compatibility-focused | None |
| services/scenespeak-agent/main.py | Prefers local OpenAI-compatible vLLM when GLM key is absent; supports allow_fallback/use_fallback. | Permanent | Tune prompt/output quality |
| services/scenespeak-agent/models.py | Suppresses Pydantic protected namespace warning. | Permanent | None |
| services/sentiment-agent/src/sentiment_agent/models.py | Suppresses Pydantic protected namespace warning. | Permanent | None |
| services/shared/cache.py | Reads REDIS_URL instead of constructing redis://redis.asyncio. | Permanent | Add unit test for env-based cache URL |
| shared/models/health.py | Suppresses Pydantic protected namespace warning. | Permanent | None |
| test_chimera_smoke.py | Exposes smoke runner to pytest while preserving direct execution. | Permanent | None |
| tests/conftest.py | Forces repo-local services imports during tests. | Permanent | None |
| tests/e2e/test_mvp_user_journeys.py | Gives live MVP concurrency test a realistic timeout. | Permanent | None |
| tests/integration/conftest.py | Removes deprecated custom event_loop fixture and corrects safety port. | Permanent | Extended-stack tests still need route cleanup |
| tests/integration/kimi/test_kimi_client.py | Supports configured Kimi host/model targets. | Permanent | None |
| tests/integration/kimi/test_kimi_super_agent.py | Targets host-published Kimi gRPC and model config. | Permanent | None |
| tests/integration/mvp/test_operator_console.py | Stabilizes operator-console integration expectations. | Permanent | None |
| tests/integration/mvp/test_service_communication.py | Handles host-vs-compose DNS differences explicitly. | Permanent | None |
| tests/performance/test_optimization_targets.py | Runs async performance tests, corrects translation port, and validates relative live concurrency. | Permanent | Add stricter host-specific budgets if desired |
| tests/resilience/test_retry.py | Stabilizes retry timing expectations. | Permanent | None |
| tests/test_monitoring_backend.py | Aligns dashboard monitoring tests with installed dependency behavior. | Permanent | None |
| tests/test_shared_middleware.py | Stabilizes middleware expectations under current dependency versions. | Permanent | None |
| tests/unit/test_chimera_core.py | Removes fragile global sys.path mutation and loads operator core by file path. | Permanent | None |
| verify_prerequisites.py | Verifies python3/current interpreter and prints venv-local commands. | Permanent | None |
| docs/reports/LOCAL_VALIDATION_REPORT.md | Publishes the final local validation evidence. | Release artifact | Refresh after future validation passes |
| docs/reports/PATCH_SUMMARY.md | Publishes this changed-files and follow-up summary. | Release artifact | Refresh when patches change |
| docs/reports/REMAINING_GAPS.md | Publishes non-blocking caveats and closure requirements. | Release artifact | Refresh as gaps close |
| docs/reports/RELEASE_SYNC_REPORT.md | Summarizes the publication pass and post-push verification procedure. | Release artifact | Refresh after future release-sync passes |

## Service Recreates Performed

* Recreated Kimi vLLM and Kimi super-agent to activate host ports 8012 and 50052.
* Recreated Kimi super-agent after token/timeout tuning.
* Rebuilt/recreated SceneSpeak after local fallback routing fix.
* Rebuilt/recreated OpenClaw after local LLM budget, in-flight lock, and Redis cache URL fixes.
* Rebuilt/refreshed the student Docker preview.

## Maintainer Follow-up

* Replace the protobuf guard removal with regenerated code and a documented cross-env protobuf pin strategy.
* Decide whether the legacy top-level extended integration tests should be updated to the MVP route or kept behind an explicit extended-stack marker.
* Configure or disable OTLP exporters in local Compose to avoid collector-unavailable log noise.
* Tune Kimi/SceneSpeak prompts and token budgets for production-quality dialogue rather than validation latency.
