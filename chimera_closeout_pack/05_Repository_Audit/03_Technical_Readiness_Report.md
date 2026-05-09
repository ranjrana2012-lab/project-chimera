# Technical Readiness Report

Status: DRAFT AUDIT REPORT - HUMAN ACTION REQUIRED.
Last refreshed: 2026-05-09.

## Detected Tech Stack

- Python 3.12.
- Operator-console CLI and web route.
- FastAPI for local web console.
- Transformers-based sentiment/generation path when dependencies and model
  access are available, with heuristic fallback.
- Docker, Compose, DGX/Kimi, and platform services exist as advanced or
  experimental routes, not the core Phase 1 close-out claim.

## Demo Status

The Phase 1 demonstrator entry points are:

- `services/operator-console/chimera_core.py`
- `services/operator-console/chimera_web.py`
- `scripts/run_phase1_demo.py`

Observed local run on 2026-05-08:

- `python3 scripts/check_environment.py` reported Python 3.12.3, Linux aarch64,
  and visible NVIDIA GB10 hardware.
- `python3 scripts/run_phase1_demo.py` loaded the DistilBERT/DistilGPT2 path on
  CPU and processed four sample inputs, including `grounding_support` and
  `reflective_transition` routes.
- The generated real-run log was written to
  `outputs/run_logs/phase1_demo_20260508T160829Z.json`.

Runtime state checked on 2026-05-09:

- NVIDIA GB10 hardware was visible locally through `nvidia-smi`.
- `chimera-kimi-vllm` / `VLLM::EngineCore` had been running for more than five
  days and was holding approximately 70 GB of GB10 GPU memory.
- `docker stop chimera-kimi-vllm` was run successfully.
- Follow-up `nvidia-smi` showed the vLLM engine was no longer present.
- `docker ps` showed other Chimera containers still running, including
  `chimera-operator-console`, `chimera-sentiment-agent`,
  `chimera-scenespeak-agent`, and `chimera-kimi-super-agent`.

Operational decision: keep Kimi/vLLM stopped for default Phase 1 close-out,
repo, docs, smoke-test, and local demo work. Restart Kimi/vLLM only for
explicit DGX/Kimi validation.

## Models Found

The code attempts to load:

- `distilbert-base-uncased-finetuned-sst-2-english`
- `distilgpt2`

If those cannot load, the demonstrator uses a heuristic fallback and must be
described as such in the demo recording.

## Scripts Created Or Improved

- `scripts/check_environment.py`
- `scripts/run_phase1_demo.py`
- `scripts/scan_for_secrets.py`
- `scripts/scan_for_overclaims.py`
- repository-relative path fixes in helper scripts.

## Logs Generated From Real Runs

Run logs should be generated under `outputs/run_logs/` by
`scripts/run_phase1_demo.py`. They are ignored by git and should be copied to
the private evidence pack only after review.

## Hardware Evidence Status

Local `nvidia-smi` and `scripts/check_environment.py` showed NVIDIA GB10
hardware on this host. That evidence does not prove grant spend, a public
deployment, or production readiness.

The stopped Kimi/vLLM container is not a blocker for the narrowed Phase 1
operator-console route. It is a blocker only for fresh DGX/Kimi validation until
the advanced route is intentionally restarted and re-tested.

## Blockers

- Human-recorded demo video is still required.
- Private evidence pack is still required.
- Scope pivot and budget reallocation approvals are still human actions.
