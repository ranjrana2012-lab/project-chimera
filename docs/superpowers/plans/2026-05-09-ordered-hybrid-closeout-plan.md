# Ordered Hybrid Close-Out Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Project Chimera stronger for a narrowed Phase 1 close-out by tightening grant-facing wording, public GitHub readiness, and local demo validation without inventing evidence.

**Architecture:** Treat `services/operator-console` as the canonical Phase 1 path. Keep close-out and evidence documents as public-safe templates or indexes, and label broader DGX/Kimi/BSL/Phase 2 surfaces as advanced or future work unless directly evidenced. Preserve private evidence outside git and keep heavy Kimi/vLLM services off unless explicitly validating that advanced route.

**Tech Stack:** Markdown documentation, Python 3.12 validation scripts, pytest, Docker runtime inspection, Git.

---

## File Structure

- Modify `docs/closeout/POINT_IN_TIME_STATUS_2026-05-08.md` to record the latest local commit state and the Kimi/vLLM resource decision.
- Modify `CODEX_COMPLETION_REPORT.md` to append a fresh autonomous-run status section rather than replacing historical results.
- Modify `evidence/PHASE_1_DELIVERED.md` to remove or soften any language that reads as final delivery or production readiness.
- Modify `evidence/evidence_pack/limitations.md` to remove "production-ready" phrasing and replace it with "proof-of-concept ready for local demonstration".
- Modify `chimera_closeout_pack/05_Repository_Audit/02_Overclaim_Scan_Report.md` with fresh scan findings and clear guarded/review categories.
- Modify `chimera_closeout_pack/05_Repository_Audit/03_Technical_Readiness_Report.md` with current GPU/container state and the decision to keep `chimera-kimi-vllm` stopped by default.
- Modify `docs/README.md` only if needed to link the Superpowers spec/plan or clarify close-out navigation.
- Create or modify no private evidence files.

## Task 1: Commit Planning Artefact

**Files:**
- Create: `docs/superpowers/plans/2026-05-09-ordered-hybrid-closeout-plan.md`
- Existing prerequisite: `docs/superpowers/specs/2026-05-09-ordered-hybrid-closeout-design.md`

- [ ] **Step 1: Check plan file exists**

Run:

```bash
test -f docs/superpowers/plans/2026-05-09-ordered-hybrid-closeout-plan.md
```

Expected: command exits with status 0.

- [ ] **Step 2: Validate markdown links and whitespace**

Run:

```bash
python3 scripts/check_markdown_links.py
git diff --check
```

Expected: no broken markdown links and no whitespace errors.

- [ ] **Step 3: Commit the plan**

Run:

```bash
git add docs/superpowers/plans/2026-05-09-ordered-hybrid-closeout-plan.md
git commit -m "docs: plan ordered hybrid close-out work"
```

Expected: local commit created; no remote push.

## Task 2: Update Point-In-Time And Completion Status

**Files:**
- Modify: `docs/closeout/POINT_IN_TIME_STATUS_2026-05-08.md`
- Modify: `CODEX_COMPLETION_REPORT.md`

- [ ] **Step 1: Write current-state updates**

Update the point-in-time status with these facts:

```text
Current local branch state after planning: main is ahead of origin/main by four or more local commits, depending on later task commits.
The advanced chimera-kimi-vllm container was stopped on 2026-05-09 because it was not required for the Phase 1 close-out route and was holding approximately 70 GB of GB10 GPU memory.
Kimi/vLLM should remain off for default close-out work and be restarted only for explicit DGX/Kimi validation.
```

Append a new dated section to `CODEX_COMPLETION_REPORT.md` rather than rewriting earlier verified results. The section heading should be:

```markdown
## 11. Autonomous Follow-Up - 2026-05-09
```

- [ ] **Step 2: Verify wording stays inside evidence boundary**

Run:

```bash
rg -n "completed public show|livestream delivered|40 students upskilled|validated accessibility|production-ready deployment|complete grant evidence" docs/closeout CODEX_COMPLETION_REPORT.md
```

Expected: any hits are in guarded "do not claim" or blocker context only.

- [ ] **Step 3: Commit status updates**

Run:

```bash
git add docs/closeout/POINT_IN_TIME_STATUS_2026-05-08.md CODEX_COMPLETION_REPORT.md
git commit -m "docs: update close-out runtime status"
```

Expected: local commit created; no remote push.

## Task 3: Tighten Public Evidence Wording

**Files:**
- Modify: `evidence/PHASE_1_DELIVERED.md`
- Modify: `evidence/evidence_pack/limitations.md`

- [ ] **Step 1: Inspect risky wording**

Run:

```bash
rg -n "production-ready|complete, working|complete BSL|validated accessibility|public show|livestream|40 students|99\\.9" evidence/PHASE_1_DELIVERED.md evidence/evidence_pack/limitations.md
```

Expected: hits identify wording to soften or mark as future/limitation.

- [ ] **Step 2: Replace unsupported maturity claims**

Use these exact replacements where the current text carries the same meaning:

```text
production-ready -> suitable for controlled local demonstration
complete, working adaptive AI framework -> Phase 1 local adaptive AI demonstrator
production-ready for its intended purpose -> ready for controlled proof-of-concept review
99.9% accuracy on test data -> accuracy target not evidenced in this public close-out snapshot
Complete BSL avatar system -> BSL/avatar system remains future-stage and unclaimed for Phase 1
```

Keep any references to public delivery, livestream, 40 students, accessibility validation, or BSL/avatar delivery framed as limitations or future work.

- [ ] **Step 3: Re-run the overclaim scan**

Run:

```bash
python3 scripts/scan_for_overclaims.py --include-untracked
```

Expected: the two edited evidence files no longer appear as unguarded maturity/accuracy/public-delivery findings.

- [ ] **Step 4: Commit public evidence wording updates**

Run:

```bash
git add evidence/PHASE_1_DELIVERED.md evidence/evidence_pack/limitations.md
git commit -m "docs: soften public evidence maturity claims"
```

Expected: local commit created; no remote push.

## Task 4: Refresh Audit Reports

**Files:**
- Modify: `chimera_closeout_pack/05_Repository_Audit/02_Overclaim_Scan_Report.md`
- Modify: `chimera_closeout_pack/05_Repository_Audit/03_Technical_Readiness_Report.md`

- [ ] **Step 1: Capture current scan facts**

Run:

```bash
python3 scripts/scan_for_overclaims.py --include-untracked
python3 scripts/scan_for_secrets.py --include-untracked
nvidia-smi
docker ps
```

Expected:

- overclaim scan completes and separates guarded close-out terms from review findings;
- secret scan completes without printing values;
- `nvidia-smi` shows GB10 with `chimera-kimi-vllm` absent;
- `docker ps` shows `chimera-kimi-vllm` stopped and other Chimera containers still running if present.

- [ ] **Step 2: Update report summaries**

`02_Overclaim_Scan_Report.md` must state:

```text
Close-out docs contain guarded "do not claim" language by design.
Remaining review findings are concentrated in legacy, Phase 2, BSL/avatar, monitoring, examples, and tests.
The Phase 1 public claim remains limited to the operator-console demonstrator unless those broader surfaces are separately evidenced.
```

`03_Technical_Readiness_Report.md` must state:

```text
NVIDIA GB10 hardware was visible locally on 2026-05-09.
The advanced chimera-kimi-vllm container was stopped because it is not required for Phase 1 close-out checks.
Kimi/vLLM should be restarted only for explicit DGX/Kimi validation.
```

- [ ] **Step 3: Commit refreshed audit reports**

Run:

```bash
git add chimera_closeout_pack/05_Repository_Audit/02_Overclaim_Scan_Report.md chimera_closeout_pack/05_Repository_Audit/03_Technical_Readiness_Report.md
git commit -m "docs: refresh close-out audit reports"
```

Expected: local commit created; no remote push.

## Task 5: Validate Phase 1 Demo Path

**Files:**
- Generated but ignored: `outputs/run_logs/*.json`
- Modify only if validation exposes a clear doc bug: `README.md`, `QUICKSTART.md`, or `docs/closeout/REPLICATION_TOOLKIT.md`

- [ ] **Step 1: Run privacy and smoke checks**

Run:

```bash
python3 scripts/privacy_preflight.py
python3 test_chimera_smoke.py
```

Expected: privacy preflight passes and smoke test reports 6 passed, 0 failed.

- [ ] **Step 2: Run focused pytest bundle**

Run:

```bash
python3 -m pytest -p no:cacheprovider tests/unit/test_chimera_core.py tests/unit/test_chimera_web_contract.py tests/unit/test_public_repo_cleanup_contract.py tests/unit/test_privacy_preflight.py -q
```

Expected: focused tests pass.

- [ ] **Step 3: Run demo wrapper**

Run:

```bash
python3 scripts/run_phase1_demo.py
```

Expected: script exits 0 and writes a new ignored JSON log under `outputs/run_logs/`.

- [ ] **Step 4: Fix only discovered doc bugs**

If a validation command fails because README, QUICKSTART, or toolkit commands are stale, patch the exact command text and re-run the failing command. Do not add new features.

- [ ] **Step 5: Commit validation-related doc fixes if any**

Run only if files changed:

```bash
git add README.md QUICKSTART.md docs/closeout/REPLICATION_TOOLKIT.md
git commit -m "docs: align phase 1 validation instructions"
```

Expected: commit only when docs changed; ignored run logs are not committed.

## Task 6: Final Safety Sweep And Local Commit Summary

**Files:**
- Modify: `CODEX_COMPLETION_REPORT.md`

- [ ] **Step 1: Run final checks**

Run:

```bash
python3 scripts/check_markdown_links.py
python3 scripts/privacy_preflight.py
git diff --check
git status --short --branch
```

Expected:

- no broken markdown links;
- privacy preflight passes;
- no whitespace errors;
- working tree shows only intentional report updates before final commit.

- [ ] **Step 2: Update final completion report section**

Append final results under `CODEX_COMPLETION_REPORT.md` section:

```markdown
## 12. Overnight Close-Out Work Results - 2026-05-09
```

Include:

- files changed;
- commands run and actual outcomes;
- whether new run logs were generated and ignored;
- whether `chimera-kimi-vllm` remains stopped;
- remaining human actions;
- local commit count ahead of origin.

- [ ] **Step 3: Commit completion report**

Run:

```bash
git add CODEX_COMPLETION_REPORT.md
git commit -m "docs: record overnight close-out results"
```

Expected: local commit created; no remote push.

- [ ] **Step 4: Report final state**

Run:

```bash
git status --short --branch
git log --oneline -8
```

Expected: branch is ahead of `origin/main`; working tree is clean or only has ignored generated logs.

## Self-Review

- Spec coverage: the plan covers grant close-out readiness, public GitHub readiness, technical demo hardening, and restrained broader repo surgery.
- Placeholder scan: no unfinished placeholder markers are used.
- Scope check: this is a single ordered close-out plan; broader dependency PRs and major service refactors are intentionally out of scope.
- Evidence boundary: every task keeps private evidence out of git and forbids invented grant facts.
