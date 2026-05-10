# Project Chimera Point-In-Time Status - 2026-05-10

Status: REPOSITORY SNAPSHOT - HUMAN REVIEW REQUIRED.

This snapshot records where Project Chimera stands after the latest local
repository close-out work. It is intended to help the owner, BCU/R&D reviewers,
and future maintainers understand what is evidenced inside the repository and
what remains outside public git.

## Executive Position

Project Chimera is now best presented as a Phase 1 local-first adaptive AI
demonstrator. The repo-supported claim is that the operator-console path can
run locally, route audience-style text into adaptive states, produce a repeatable
CLI/web demonstration path, and support a cautious close-out documentation pack.

The repository is not the final grant submission pack. It does not contain
private financial evidence, written scope approval, a signed MFA declaration, or
a human-recorded demo video.

## Current Git Position

- Branch: `main`.
- Local state at time of this snapshot: ahead of `origin/main` by local commits.
- Remote push: not performed in this pass.
- Latest local cleanup commits include:
  - `b7395e9c chore: remove public local path and secret scan findings`
  - `f96f8aa9 docs: tighten phase 1 overclaim boundaries`
  - `3c154730 docs: record overnight close-out results`

## What Is Completed In The Repository

### Phase 1 Technical Demonstrator

- `services/operator-console/chimera_core.py` provides the main Phase 1 local
  adaptive demonstrator path.
- `services/operator-console/chimera_web.py` exposes the local FastAPI console
  route.
- `scripts/run_phase1_demo.py` runs a repeatable Phase 1 evidence-capture flow
  and writes real run logs to ignored `outputs/run_logs/` files.
- The current evidenced demo states include:
  - `supportive_care`
  - `momentum_build`
  - `grounding_support`
  - `reflective_transition`
  - `standard_response`

### Close-Out Documentation

- `docs/closeout/SUBMISSION_READINESS.md`
- `docs/closeout/CASE_STUDY_PHASE1.md`
- `docs/closeout/REPLICATION_TOOLKIT.md`
- `docs/closeout/EVIDENCE_PACK_INDEX.md`
- `docs/closeout/CLAIMS_REGISTER.md`
- `chimera_closeout_pack/`
- `CODEX_COMPLETION_REPORT.md`

These files frame the project as a Phase 1 demonstrator and separate
repo-supported evidence from human-supplied private evidence.

### Public/Private Boundary Tooling

- `scripts/privacy_preflight.py` checks for private grant/evidence paths before
  public release.
- `scripts/scan_for_secrets.py` checks tracked and untracked public-safe text
  for secret-like values without printing values.
- `scripts/scan_for_overclaims.py` checks public text for risky close-out
  claims and distinguishes guarded wording from Phase 2 / experimental surfaces.

### Public Wording Cleanup

- `CONTRIBUTORS.md` no longer claims a completed student cohort or release
  community that is not evidenced.
- The BSL/avatar service README now identifies that folder as future-stage
  research and not part of the evidenced Phase 1 demonstrator.
- The educational-platform implementation summary now identifies that folder as
  historical/experimental and not a current Phase 1 close-out claim.
- Generic service-template maturity wording has been softened.
- Public local machine paths have been replaced with `<repo>`, `$HOME`,
  `Path.home()`, or environment-variable based defaults.
- Example secret-like literals have been replaced with placeholders.

## Latest Local Validation

Commands run during the latest cleanup pass:

| Command | Result |
| --- | --- |
| `python3 scripts/scan_for_secrets.py --include-untracked --fail-on-findings` | Passed: no secret-like findings found |
| `python3 scripts/privacy_preflight.py` | Passed |
| `python3 scripts/scan_for_overclaims.py --include-untracked --fail-on-review` | Passed: guarded and `experimental_or_phase2` findings remain, no unresolved `review` findings |
| `python3 -m pytest -p no:cacheprovider tests/unit/test_chimera_core.py tests/unit/test_chimera_web_contract.py tests/unit/test_public_repo_cleanup_contract.py tests/unit/test_privacy_preflight.py -q` | 45 passed |
| `python3 test_chimera_smoke.py` | 6 passed, 0 failed |
| `python3 -m pytest -p no:cacheprovider platform/cicd-gateway/tests/test_webhook.py tests/test_alertmanager_config.py services/scenespeak-agent/tests/test_metrics.py services/scenespeak-agent/tests/test_tracing.py -q` | 60 passed; emitted an OpenTelemetry exporter shutdown warning after completion |
| `python3 scripts/check_markdown_links.py` | No broken markdown links |
| `git diff --check` | Passed |

## Current Claim Boundary

Safe repo-supported wording:

- Phase 1 local-first adaptive AI demonstrator.
- Controlled local demo or simulation.
- Reusable technical documentation and setup guidance.
- Open-source-ready code assets, subject to human review and push/release.
- Designed for future audience input.

Guardrails:

- Do not claim public show delivered.
- Do not claim livestream delivered.
- Do not claim 40 students participated or were upskilled unless separate
  evidence is supplied.
- Do not claim validated accessibility testing.
- Do not claim two DGX units.
- Do not claim production deployment.
- Do not claim completed BSL/avatar delivery.
- Do not claim final grant evidence pack completion.

## Remaining Human Actions

Critical blockers outside the repository:

- Send scope pivot / clarification emails to Sisi Yuen, James Green, and Laura.
- Obtain written BCU/partner response before claiming agreement or approval.
- Record a 3-5 minute narrated demo video showing the local adaptive pipeline.
- Store screenshots, run logs, and the demo video privately.
- Provide actual invoices addressed to Secure-Wireless Ltd.
- Provide redacted bank statements showing date, payee, and amount.
- Complete and sign the MFA declaration using the approved form or wording.
- Confirm any BCU approval required for budget reallocation.
- Add approved BCU/AHRC acknowledgement wording.
- Review all close-out drafts before submission.

## Recommended Next Repository Steps

1. Keep Kimi/vLLM stopped unless explicitly validating the DGX/Kimi route.
2. Run the privacy, secret, overclaim, smoke, and focused pytest checks before
   any public push.
3. Decide whether to push the current public-safe commits to GitHub.
4. If wider due-diligence review is expected, consider archiving or further
   labelling Phase 2 services, monitoring dashboards, and historical test
   surfaces.

## Recommended Next Human Step

The single most important human action is to send the scope pivot /
pre-submission clarification emails and retain the sent emails and responses
privately. The Phase 1 framing and any budget reallocation should not be treated
as accepted until written correspondence exists.
