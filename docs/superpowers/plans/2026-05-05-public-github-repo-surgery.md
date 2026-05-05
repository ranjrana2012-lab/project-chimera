# Public GitHub Repository Surgery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the public GitHub repository clean, reviewer-friendly, and safe to publish by simplifying public docs, removing tracked private/generated/experimental clutter, and documenting GitHub hygiene actions.

**Architecture:** Build from the clean `release-hardening-closeout` branch. Add a public repository contract test first, then make it pass with docs, report relocation, tracked artifact removal, and GitHub metadata cleanup. Remote branch deletion and GitHub settings changes are documented as owner actions and happen after merge.

**Tech Stack:** Git, Markdown, Python 3.12, pytest, existing `scripts/privacy_preflight.py`, GitHub repository metadata files.

---

## File Structure

Create:

- `tests/unit/test_public_repo_cleanup_contract.py` - guard tests for public repo shape, forbidden tracked paths, README stale phrases, report relocation, and template duplicates.
- `docs/reports/README.md` - maintainer-facing validation report index.
- `docs/github/REPOSITORY_SETTINGS.md` - GitHub settings checklist that cannot be applied safely by file edits alone.
- `docs/github/BRANCH_CLEANUP_RUNBOOK.md` - post-merge branch cleanup procedure.

Modify:

- `README.md` - concise public landing page.
- `docs/README.md` - documentation hub.
- `docs/guides/README.md` - runtime profile guide index.
- `CONTRIBUTING.md` - shorter Python 3.12 contributor guide.
- `CHANGELOG.md` - release/tag wording aligned with existing tags.
- `.gitignore` - ignore remaining experiment/local artifact paths.
- `scripts/privacy_preflight.py` - classify public-tracked experiments and root machine reports as publication risks.
- `tests/unit/test_privacy_preflight.py` - add classifier coverage for experiment/report paths.
- `.github/ISSUE_TEMPLATE/*` - keep one bug template and one feature template.
- `.github/CODEOWNERS` - confirm/clean ownership entries.
- `.github/PULL_REQUEST_TEMPLATE.md` - require privacy preflight and public docs review.

Move:

- `LOCAL_VALIDATION_REPORT.md` -> `docs/reports/LOCAL_VALIDATION_REPORT.md`
- `PATCH_SUMMARY.md` -> `docs/reports/PATCH_SUMMARY.md`
- `REMAINING_GAPS.md` -> `docs/reports/REMAINING_GAPS.md`
- `RELEASE_SYNC_REPORT.md` -> `docs/reports/RELEASE_SYNC_REPORT.md`

Remove from public tracking:

- `.autonomous/`
- `.claude/`
- `future_concepts/`
- `demo-materials-2026-03-02/`
- `progress/`
- `proposals/`
- `internal/grant-tracking/grant_closeout/`
- any remaining tracked `node_modules`, coverage, test-results, token JSON, compiled local binaries, generated captures, and non-example `.env` files.

Do not modify in this pass:

- service/package path names such as `kimi-super-agent`;
- Docker Compose file locations;
- Kubernetes directory layout unless a reference scan proves a path is unused;
- remote branches.

---

### Task 1: Add Public Repository Cleanup Contract Test

**Files:**
- Create: `tests/unit/test_public_repo_cleanup_contract.py`

- [ ] **Step 1: Write the failing public repo contract test**

Create `tests/unit/test_public_repo_cleanup_contract.py` with this content:

```python
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


FORBIDDEN_TRACKED_PREFIXES = (
    ".autonomous/",
    ".claude/",
    "demo-materials-2026-03-02/",
    "future_concepts/",
    "internal/",
    "platform/dashboard/frontend/node_modules/",
    "progress/",
    "proposals/",
    "services/operator-console/demo_captures/",
)


FORBIDDEN_TRACKED_EXACT = {
    ".env.docker",
    ".env.nemotron",
    "LOCAL_VALIDATION_REPORT.md",
    "PATCH_SUMMARY.md",
    "RELEASE_SYNC_REPORT.md",
    "REMAINING_GAPS.md",
    "services/zai-auth-proxy/tokens/session_token.json",
}


FORBIDDEN_README_PHRASES = (
    "Last validated locally",
    "Last locally validated",
    "737 passed",
    "96 skipped",
    "Monitoring Stack",
    "Validated Checks",
    "docker login nvcr.io",
    "Download Kimi K2.6 model",
    "LOCAL_VALIDATION_REPORT.md",
    "PATCH_SUMMARY.md",
    "RELEASE_SYNC_REPORT.md",
    "REMAINING_GAPS.md",
)


REQUIRED_README_PHRASES = (
    "Project Chimera",
    "Phase 1",
    "local adaptive AI foundation",
    "Student / Laptop",
    "Private evidence",
    "docs/guides/STUDENT_LAPTOP_SETUP.md",
    "docs/guides/DGX_SPARK_SETUP.md",
    "docs/guides/KIMI_QUICKSTART.md",
)


def git_ls_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_public_git_index_excludes_private_generated_and_experimental_paths():
    tracked = set(git_ls_files())

    forbidden = {
        path
        for path in tracked
        if path in FORBIDDEN_TRACKED_EXACT
        or any(path.startswith(prefix) for prefix in FORBIDDEN_TRACKED_PREFIXES)
        or "/node_modules/" in path
        or path.endswith("/coverage.json")
        or path.endswith("/test-results/.last-run.json")
    }

    assert forbidden == set()


def test_validation_reports_are_under_docs_reports_not_root():
    tracked = set(git_ls_files())

    assert "LOCAL_VALIDATION_REPORT.md" not in tracked
    assert "PATCH_SUMMARY.md" not in tracked
    assert "REMAINING_GAPS.md" not in tracked
    assert "RELEASE_SYNC_REPORT.md" not in tracked
    assert "docs/reports/README.md" in tracked
    assert "docs/reports/LOCAL_VALIDATION_REPORT.md" in tracked
    assert "docs/reports/PATCH_SUMMARY.md" in tracked
    assert "docs/reports/REMAINING_GAPS.md" in tracked
    assert "docs/reports/RELEASE_SYNC_REPORT.md" in tracked


def test_readme_is_concise_public_landing_page():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for phrase in FORBIDDEN_README_PHRASES:
        assert phrase not in readme
    for phrase in REQUIRED_README_PHRASES:
        assert phrase in readme
    assert len(readme.splitlines()) <= 180


def test_github_issue_templates_are_deduplicated():
    templates = {
        path.name
        for path in (REPO_ROOT / ".github" / "ISSUE_TEMPLATE").glob("*")
        if path.is_file()
    }

    assert "bug_report.md" in templates
    assert "feature_request.md" in templates
    assert "bug.md" not in templates
    assert "feature.md" not in templates
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
/home/ranj/Project_Chimera/services/operator-console/venv/bin/python -m pytest tests/unit/test_public_repo_cleanup_contract.py -q
```

Expected: failure showing currently tracked forbidden paths, root report files,
stale README phrases, or duplicate issue templates.

- [ ] **Step 3: Commit the red contract test**

Run:

```bash
git add tests/unit/test_public_repo_cleanup_contract.py
git commit -m "test: add public repo cleanup contract"
```

Expected: one new test file committed. The test is allowed to fail until later
tasks make it pass.

---

### Task 2: Extend Privacy Preflight For Public Repo Surgery

**Files:**
- Modify: `scripts/privacy_preflight.py`
- Modify: `tests/unit/test_privacy_preflight.py`

- [ ] **Step 1: Add failing classifier coverage**

Append this test to `tests/unit/test_privacy_preflight.py`:

```python
def test_public_cleanup_experiment_and_root_report_paths_are_rejected():
    privacy_preflight = load_privacy_preflight()

    findings = privacy_preflight.classify_paths(
        [
            ".autonomous/state.json",
            ".claude/settings.local.json",
            "future_concepts/services/old-agent/app.py",
            "demo-materials-2026-03-02/raw_capture.txt",
            "progress/week-1.md",
            "proposals/venue-proposal.md",
            "LOCAL_VALIDATION_REPORT.md",
            "PATCH_SUMMARY.md",
            "REMAINING_GAPS.md",
            "RELEASE_SYNC_REPORT.md",
            "docs/reports/LOCAL_VALIDATION_REPORT.md",
            "docs/reports/PATCH_SUMMARY.md",
        ]
    )

    assert {finding.path for finding in findings} == {
        ".autonomous/state.json",
        ".claude/settings.local.json",
        "future_concepts/services/old-agent/app.py",
        "demo-materials-2026-03-02/raw_capture.txt",
        "progress/week-1.md",
        "proposals/venue-proposal.md",
        "LOCAL_VALIDATION_REPORT.md",
        "PATCH_SUMMARY.md",
        "REMAINING_GAPS.md",
        "RELEASE_SYNC_REPORT.md",
    }
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
/home/ranj/Project_Chimera/services/operator-console/venv/bin/python -m pytest tests/unit/test_privacy_preflight.py::test_public_cleanup_experiment_and_root_report_paths_are_rejected -q
```

Expected: failure because those public cleanup paths are not all classified yet.

- [ ] **Step 3: Update the classifier**

In `scripts/privacy_preflight.py`, add constants near the existing keyword
constants:

```python
PUBLIC_EXPERIMENT_PREFIXES = (
    ".autonomous/",
    ".claude/",
    "demo-materials-2026-03-02/",
    "future_concepts/",
    "progress/",
    "proposals/",
)

ROOT_REPORT_FILES = {
    "LOCAL_VALIDATION_REPORT.md",
    "PATCH_SUMMARY.md",
    "RELEASE_SYNC_REPORT.md",
    "REMAINING_GAPS.md",
}
```

In `classify_paths()`, add these branches after the `internal/` branch:

```python
        elif any(path.startswith(prefix) for prefix in PUBLIC_EXPERIMENT_PREFIXES):
            reason = "public experiment or prototype path"
        elif path in ROOT_REPORT_FILES:
            reason = "root maintainer report path"
```

- [ ] **Step 4: Run privacy preflight tests**

Run:

```bash
/home/ranj/Project_Chimera/services/operator-console/venv/bin/python -m pytest tests/unit/test_privacy_preflight.py -q
```

Expected: all privacy preflight tests pass.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/privacy_preflight.py tests/unit/test_privacy_preflight.py
git commit -m "test: extend privacy gate for public repo cleanup"
```

---

### Task 3: Rewrite Public README And Docs Indexes

**Files:**
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/guides/README.md`

- [ ] **Step 1: Replace `README.md` with concise public landing content**

Replace `README.md` with:

````markdown
# Project Chimera

Project Chimera is an AI-powered live theatre research platform. Phase 1 is a
local adaptive AI foundation: it accepts audience-style text, detects emotional
tone, routes the input to an adaptive response strategy, and exposes a small CLI
and web console for review.

[![CI/CD](https://github.com/ranjrana2012-lab/project-chimera/actions/workflows/ci.yml/badge.svg)](https://github.com/ranjrana2012-lab/project-chimera/actions/workflows/ci.yml)
![Release](https://img.shields.io/github/v/tag/ranjrana2012-lab/project-chimera?label=release)
![Python](https://img.shields.io/badge/python-3.12-blue)

## Phase 1 Status

The current public claim is deliberately narrow: Project Chimera has a working
local adaptive AI demonstrator and supporting service experiments. It is not yet
a finished theatre production, public audience workflow, BSL/avatar system, or
complete grant evidence pack.

## What The Local Demo Shows

- Sentiment routing for positive, negative, and neutral text.
- Adaptive strategies: `momentum_build`, `supportive_care`, and
  `standard_response`.
- Baseline-versus-adaptive comparison mode.
- Caption-style output and SRT export.
- A lightweight operator-console web route with state, process, and CSV export
  endpoints.

## Quick Start: Student / Laptop

Use this route first on ordinary Windows, macOS, Linux, or WSL machines.

```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

cd services/operator-console
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python chimera_core.py demo
```

On Windows PowerShell, use `.\venv\Scripts\python.exe` instead of
`./venv/bin/python`.

To run the local web console:

```bash
cd services/operator-console
PORT=18080 ./venv/bin/python chimera_web.py
```

Open `http://127.0.0.1:18080`.

## Setup Guides

- Student / Laptop: `docs/guides/STUDENT_LAPTOP_SETUP.md`
- DGX Spark / GB10: `docs/guides/DGX_SPARK_SETUP.md`
- Kimi advanced route: `docs/guides/KIMI_QUICKSTART.md`
- Developer setup: `docs/DEVELOPER_SETUP.md`

Use the Student / Laptop route unless you have clear DGX Spark / GB10 hardware
evidence and Docker GPU access.

## Private Evidence

The public repository contains source, tests, setup docs, and public-safe
templates. Private evidence stays outside public git:

- receipts and invoices;
- private grant records;
- meeting notes;
- generated screenshots, recordings, and logs;
- participant data;
- API keys, tokens, and `.env` files.

Local private evidence should live under `internal/` or another private storage
location. Run `scripts/privacy_preflight.py` before publishing.

## Repository Map

```text
services/operator-console/  Phase 1 local CLI and web demonstrator
services/                   Experimental and advanced service components
tests/                      Unit, integration, and smoke tests
docs/                       Documentation hub and setup guides
scripts/                    Validation, setup, and maintenance helpers
demos/                      Public-safe demo scripts and checklists
evidence/                   Public-safe placeholders only
```

## Contributing

See `CONTRIBUTING.md` for branch naming, local validation, and PR expectations.
See `SECURITY.md` for vulnerability reporting.

## License

MIT License.
````

- [ ] **Step 2: Replace `docs/README.md` with a docs hub**

Replace `docs/README.md` with:

````markdown
# Project Chimera Documentation

This directory is the public documentation hub. Start with the default local
reviewer route, then use advanced guides only when the machine and credentials
match the route.

## Start Here

- `guides/STUDENT_LAPTOP_SETUP.md` - default setup for students, reviewers, and
  ordinary laptops/desktops.
- `DEVELOPER_SETUP.md` - developer environment and repository orientation.
- `guides/DGX_SPARK_SETUP.md` - advanced DGX Spark / GB10 setup.
- `guides/KIMI_QUICKSTART.md` - advanced Kimi route.

## Architecture And APIs

- `architecture/overview.md`
- `architecture/services.md`
- `api/README.md`
- `api/operator-console.md`

## Maintainer Reports

- `reports/README.md`

Maintainer reports are validation history and caveats. They are not the default
setup path for new users.

## Demo And Evidence Guidance

- `demo/README.md`
- `demo/demo-script.md`
- `guides/STUDENT_LAPTOP_SETUP.md`
````

- [ ] **Step 3: Replace `docs/guides/README.md` with a runtime profile index**

Replace `docs/guides/README.md` with:

````markdown
# Setup Guides

Choose the route from local evidence.

## Default Route

- `STUDENT_LAPTOP_SETUP.md`

Use this for students, reviewers, Windows, macOS, WSL, ordinary Linux laptops,
and any machine where Docker or GPU access is unavailable or uncertain.

## Advanced Routes

- `DGX_SPARK_SETUP.md`
- `KIMI_QUICKSTART.md`

Use these only when the host evidence supports DGX Spark / GB10-class hardware,
ARM64 Linux, Docker, Docker GPU access, and any required registry/model access.

## Developer Reference

- `DEVELOPMENT.md`
- `TESTING.md`
- `DOCKER.md`
- `github-workflow.md`
````

- [ ] **Step 4: Run README contract test**

Run:

```bash
/home/ranj/Project_Chimera/services/operator-console/venv/bin/python -m pytest tests/unit/test_public_repo_cleanup_contract.py::test_readme_is_concise_public_landing_page -q
```

Expected: README test passes or reports exact missing/stale phrases.

- [ ] **Step 5: Commit**

Run:

```bash
git add README.md docs/README.md docs/guides/README.md
git commit -m "docs: simplify public readme and docs indexes"
```

---

### Task 4: Move Maintainer Reports Under `docs/reports`

**Files:**
- Move: `LOCAL_VALIDATION_REPORT.md`
- Move: `PATCH_SUMMARY.md`
- Move: `REMAINING_GAPS.md`
- Move: `RELEASE_SYNC_REPORT.md`
- Create: `docs/reports/README.md`

- [ ] **Step 1: Create reports directory and move reports**

Run:

```bash
mkdir -p docs/reports
git mv LOCAL_VALIDATION_REPORT.md docs/reports/LOCAL_VALIDATION_REPORT.md
git mv PATCH_SUMMARY.md docs/reports/PATCH_SUMMARY.md
git mv REMAINING_GAPS.md docs/reports/REMAINING_GAPS.md
git mv RELEASE_SYNC_REPORT.md docs/reports/RELEASE_SYNC_REPORT.md
```

Expected: four root reports are staged as renames.

- [ ] **Step 2: Add reports index**

Create `docs/reports/README.md`:

```markdown
# Maintainer Validation Reports

These reports capture local validation history, repair summaries, and remaining
caveats. They are maintainer-facing records, not first-run setup instructions.

Use `../guides/STUDENT_LAPTOP_SETUP.md` for the default reviewer setup route.

## Reports

- `LOCAL_VALIDATION_REPORT.md`
- `PATCH_SUMMARY.md`
- `REMAINING_GAPS.md`
- `RELEASE_SYNC_REPORT.md`

Do not store private grant records, receipts, invoices, screenshots, recordings,
or generated evidence logs in this directory.
```

- [ ] **Step 3: Update root report references**

Run:

```bash
rg -n "LOCAL_VALIDATION_REPORT|PATCH_SUMMARY|REMAINING_GAPS|RELEASE_SYNC_REPORT" .
```

For public docs that should keep a report reference, change root paths to
`docs/reports/<filename>`. Do not add report links back to the top of
`README.md`.

- [ ] **Step 4: Run report contract test**

Run:

```bash
/home/ranj/Project_Chimera/services/operator-console/venv/bin/python -m pytest tests/unit/test_public_repo_cleanup_contract.py::test_validation_reports_are_under_docs_reports_not_root -q
```

Expected: report relocation test passes.

- [ ] **Step 5: Commit**

Run:

```bash
git add docs/reports
git add -u LOCAL_VALIDATION_REPORT.md PATCH_SUMMARY.md REMAINING_GAPS.md RELEASE_SYNC_REPORT.md
git commit -m "docs: move maintainer validation reports under docs reports"
```

---

### Task 5: Remove Public-Tracked Experiments And Generated Artifacts

**Files:**
- Modify: `.gitignore`
- Remove from tracking: experiment and generated paths listed in the design.

- [ ] **Step 1: Add remaining public cleanup ignore rules**

In `.gitignore`, add these lines under `# Grant Materials & Private Demo Outputs`:

```gitignore
demo-materials-2026-03-02/
future_concepts/
progress/
proposals/
*.mp4
*.webm
*.mov
*.mkv
*.avi
*.m4v
```

The existing `.gitignore` already covers `.autonomous/`, `.claude/`,
`internal/`, `node_modules`, `coverage.json`, `test-results`, generated evidence,
and non-example `.env` files.

- [ ] **Step 2: Scan references before removal**

Run:

```bash
rg -n "\.autonomous|\.claude|future_concepts|demo-materials-2026-03-02|progress/|proposals/|internal/grant-tracking/grant_closeout" README.md docs scripts tests services .github AGENTS.md
```

Expected: output lists any public references. Update references that point to
removed public paths. Keep references only when they explain that those paths are
private/local and ignored.

- [ ] **Step 3: Remove tracked paths from public git**

Run:

```bash
git rm -r --cached --ignore-unmatch .autonomous .claude future_concepts demo-materials-2026-03-02 progress proposals internal/grant-tracking/grant_closeout
git rm -r --cached --ignore-unmatch platform/dashboard/frontend/node_modules services/operator-console/demo_captures services/zai-auth-proxy/tokens/session_token.json services/claude-orchestrator/bin services/claude-orchestrator/orchestrator services/nemoclaw-orchestrator/coverage.json future_concepts/services/simulation-engine/coverage.json services/safety-filter/test-results/.last-run.json .env.docker .env.nemotron
```

Expected: tracked paths are staged as deleted. Ignored working copies may remain
locally.

- [ ] **Step 4: Run public repo contract path test**

Run:

```bash
/home/ranj/Project_Chimera/services/operator-console/venv/bin/python -m pytest tests/unit/test_public_repo_cleanup_contract.py::test_public_git_index_excludes_private_generated_and_experimental_paths -q
```

Expected: forbidden tracked path test passes.

- [ ] **Step 5: Run privacy preflight**

Run:

```bash
/home/ranj/Project_Chimera/services/operator-console/venv/bin/python scripts/privacy_preflight.py
```

Expected: `Privacy preflight passed.`

- [ ] **Step 6: Commit**

Run:

```bash
git add .gitignore
git add -u
git commit -m "chore: remove public tracked experiments and generated artifacts"
```

---

### Task 6: Tidy GitHub Templates And Repository Settings Docs

**Files:**
- Modify: `.github/ISSUE_TEMPLATE/bug_report.md`
- Modify: `.github/ISSUE_TEMPLATE/feature_request.md`
- Remove: `.github/ISSUE_TEMPLATE/bug.md`
- Remove: `.github/ISSUE_TEMPLATE/feature.md`
- Modify: `.github/PULL_REQUEST_TEMPLATE.md`
- Modify: `.github/CODEOWNERS`
- Create: `docs/github/REPOSITORY_SETTINGS.md`
- Create: `docs/github/BRANCH_CLEANUP_RUNBOOK.md`

- [ ] **Step 1: Remove duplicate issue templates**

Run:

```bash
git rm .github/ISSUE_TEMPLATE/bug.md .github/ISSUE_TEMPLATE/feature.md
```

Expected: duplicate legacy templates are staged for deletion.

- [ ] **Step 2: Ensure bug report template asks for route and validation**

Edit `.github/ISSUE_TEMPLATE/bug_report.md` so it includes these headings:

```markdown
## Runtime Route

- [ ] Student / Laptop
- [ ] DGX Spark / GB10
- [ ] Kimi advanced route
- [ ] Other

## What Happened

## Expected Behaviour

## Reproduction Steps

## Validation Output

Paste relevant command output from `verify_prerequisites.py`,
`test_chimera_smoke.py`, or the failing test.

## Privacy Check

- [ ] I have not attached private grant records, receipts, invoices, tokens,
      participant data, or `.env` files.
```

- [ ] **Step 3: Ensure feature request template separates public and private material**

Edit `.github/ISSUE_TEMPLATE/feature_request.md` so it includes:

```markdown
## Proposed Feature

## User Or Reviewer Need

## Runtime Route

- [ ] Student / Laptop
- [ ] DGX Spark / GB10
- [ ] Kimi advanced route
- [ ] Documentation only

## Scope

## Privacy Notes

- [ ] This request does not require publishing private grant records, receipts,
      invoices, tokens, participant data, or `.env` files.
```

- [ ] **Step 4: Update PR template**

Ensure `.github/PULL_REQUEST_TEMPLATE.md` includes:

```markdown
## Validation

- [ ] `scripts/privacy_preflight.py`
- [ ] `verify_prerequisites.py`
- [ ] `test_chimera_smoke.py`
- [ ] focused pytest command:

## Public/Private Boundary

- [ ] No private grant records, receipts, invoices, recordings, screenshots,
      tokens, participant data, or `.env` files are included.
- [ ] Generated evidence is stored privately, not committed.

## Runtime Route

- [ ] Student / Laptop
- [ ] DGX Spark / GB10
- [ ] Kimi advanced route
- [ ] Documentation only
```

- [ ] **Step 5: Add repository settings doc**

Create `docs/github/REPOSITORY_SETTINGS.md`:

```markdown
# GitHub Repository Settings

These settings require repository owner access. They are not completed by file
edits alone.

## Branch Protection For `main`

- Require pull request before merge.
- Require at least one approving review.
- Require status checks to pass before merge.
- Require the active CI workflow.
- Dismiss stale approvals when new commits are pushed.
- Restrict force pushes.
- Restrict deletions.

## Repository Hygiene

- Enable secret scanning.
- Enable Dependabot alerts.
- Enable automatic deletion of merged branches.
- Add repository description: `AI-powered live theatre research platform with a local adaptive Phase 1 demonstrator`.
- Add topics: `ai`, `theatre`, `adaptive-ai`, `fastapi`, `docker`, `research`.

## Releases

- Use `CHANGELOG.md` as the release source.
- Publish GitHub Releases for stable tags.
- Keep `v1.0.0-phase1` as the Phase 1 public milestone tag unless a newer
  reviewed release supersedes it.
```

- [ ] **Step 6: Add branch cleanup runbook**

Create `docs/github/BRANCH_CLEANUP_RUNBOOK.md`:

````markdown
# Branch Cleanup Runbook

Run this after the public cleanup branch is merged.

## Safety Checks

```bash
git fetch --all --prune
git ls-remote --heads origin
```

For each candidate branch, confirm:

- no open pull request targets or uses the branch;
- no unique commits need to be preserved;
- the repository owner agrees to deletion or legacy tagging.

## Candidate Branches

- `origin/codex-chimera-validation-fixes-20260424`
- `origin/codex/student-dgx-runtime-profiles`
- `origin/master`

## Deletion Commands

Only run these after the safety checks pass:

```bash
git push origin --delete codex-chimera-validation-fixes-20260424
git push origin --delete codex/student-dgx-runtime-profiles
```

Before changing `master`, tag its current commit:

```bash
git fetch origin master
git tag legacy-master-20260505 origin/master
git push origin legacy-master-20260505
```

Delete `master` only after confirming GitHub default branch is `main` and no
automation still references `master`.
````

- [ ] **Step 7: Run template contract test**

Run:

```bash
/home/ranj/Project_Chimera/services/operator-console/venv/bin/python -m pytest tests/unit/test_public_repo_cleanup_contract.py::test_github_issue_templates_are_deduplicated -q
```

Expected: issue template de-duplication test passes.

- [ ] **Step 8: Commit**

Run:

```bash
git add .github docs/github
git commit -m "chore: tidy github templates and repository settings docs"
```

---

### Task 7: Update Contributing And Changelog Guidance

**Files:**
- Modify: `CONTRIBUTING.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Replace `CONTRIBUTING.md` with a shorter contributor guide**

Replace `CONTRIBUTING.md` with:

````markdown
# Contributing To Project Chimera

Project Chimera welcomes focused, tested contributions. Keep public/private
boundaries clear: do not commit private grant records, receipts, invoices,
tokens, participant data, generated evidence, or `.env` files.

## Code Of Conduct

Follow `CODE_OF_CONDUCT.md`.

## Default Setup

Use Python 3.12.

```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera
cd services/operator-console
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python chimera_core.py demo
```

Windows users should follow `docs/guides/STUDENT_LAPTOP_SETUP.md`.

## Branch Naming

- `feature/<name>`
- `fix/<name>`
- `docs/<name>`
- `chore/<name>`

## Before Opening A Pull Request

Run the checks that match your change:

```bash
./services/operator-console/venv/bin/python verify_prerequisites.py
./services/operator-console/venv/bin/python test_chimera_smoke.py
./services/operator-console/venv/bin/python scripts/privacy_preflight.py
./services/operator-console/venv/bin/python -m pytest tests/unit -q
```

For narrow changes, run the focused test files you touched and explain the
scope in the PR.

## Pull Request Expectations

- Keep changes focused.
- Include tests for behavior changes.
- Update docs when user-facing commands or routes change.
- Mention whether the change affects Student / Laptop, DGX Spark / GB10, Kimi,
  or documentation-only routes.
- Confirm no private evidence or generated artifacts are committed.

## More Detail

- Developer setup: `docs/DEVELOPER_SETUP.md`
- Student setup: `docs/guides/STUDENT_LAPTOP_SETUP.md`
- GitHub workflow: `docs/guides/github-workflow.md`
- Security policy: `SECURITY.md`
````

- [ ] **Step 2: Update `CHANGELOG.md` release wording**

Edit the top of `CHANGELOG.md` so it includes:

```markdown
# Changelog

All notable public changes to Project Chimera are documented here.

## Unreleased

- Public repository cleanup in progress.
- README and contributor-facing docs simplified.
- Private/generated artifacts kept out of public git through privacy preflight.

## v1.0.0-phase1

- Phase 1 local adaptive AI foundation milestone.
- Student / Laptop route documented as the default reviewer path.
- DGX Spark / GB10 and Kimi routes documented as advanced routes.
```

Keep any existing useful historical entries below this section.

- [ ] **Step 3: Run reference checks**

Run:

```bash
rg -n "Python 3\.10|python 3\.10|status-active|version-1\.0\.0|Last validated locally|737 passed|96 skipped" README.md CONTRIBUTING.md CHANGELOG.md docs
```

Expected: no stale matches in public landing or contributing docs. If matches
remain in maintainer reports under `docs/reports/`, leave them only when they
are historical records.

- [ ] **Step 4: Commit**

Run:

```bash
git add CONTRIBUTING.md CHANGELOG.md
git commit -m "docs: update contributing branch and release guidance"
```

---

### Task 8: Workflow Inventory And Conservative Cleanup

**Files:**
- Create: `docs/github/WORKFLOW_INVENTORY.md`
- Optionally remove only clearly duplicate workflow files after trigger review.

- [ ] **Step 1: Capture workflow triggers**

Run:

```bash
for f in .github/workflows/*; do printf '\n## %s\n' "$f"; sed -n '1,80p' "$f"; done
```

Expected: review the triggers and job names for each workflow.

- [ ] **Step 2: Create workflow inventory**

Create `docs/github/WORKFLOW_INVENTORY.md`:

```markdown
# Workflow Inventory

This inventory records the CI/CD workflow state during the public repository
cleanup.

## Active Baseline

- `.github/workflows/ci.yml` is the public README badge target and should remain
  active for pushes and pull requests to `main`.

## Review Before Removal

The repository contains multiple historical CI, test, deploy, onboarding, and
trust-check workflows. Remove a workflow only after confirming:

- its trigger duplicates another maintained workflow;
- no README, branch protection rule, or repository setting references it;
- the owner agrees that the automation is obsolete.

## Deferred Cleanup

Workflow consolidation is deferred when trigger ownership is unclear.
```

- [ ] **Step 3: Remove no workflows unless duplication is certain**

If `.github/workflows/ci.yaml` has the same trigger and same purpose as
`.github/workflows/ci.yml`, remove only `ci.yaml`:

```bash
git rm .github/workflows/ci.yaml
```

If the trigger or job purpose differs, keep both and document the reason in
`docs/github/WORKFLOW_INVENTORY.md`.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/github/WORKFLOW_INVENTORY.md .github/workflows
git commit -m "docs: document github workflow inventory"
```

Expected: commit includes workflow documentation and only proven-safe workflow
removals.

---

### Task 9: Full Validation And Public Safety Gate

**Files:**
- No intended source modifications.

- [ ] **Step 1: Run focused test suite**

Run:

```bash
/home/ranj/Project_Chimera/services/operator-console/venv/bin/python -m pytest -p no:cacheprovider tests/unit/test_public_repo_cleanup_contract.py tests/unit/test_privacy_preflight.py tests/unit/test_phase1_evidence_capture.py tests/unit/test_capture_demo_claims.py tests/unit/test_chimera_cli_contract.py tests/unit/test_chimera_web_contract.py test_chimera_smoke.py -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run prerequisite and smoke validation**

Run:

```bash
/home/ranj/Project_Chimera/services/operator-console/venv/bin/python verify_prerequisites.py
/home/ranj/Project_Chimera/services/operator-console/venv/bin/python test_chimera_smoke.py
```

Expected: prerequisites report zero failures, smoke tests report 6/6 passing.

- [ ] **Step 3: Run privacy preflight**

Run:

```bash
/home/ranj/Project_Chimera/services/operator-console/venv/bin/python scripts/privacy_preflight.py
```

Expected: `Privacy preflight passed.`

- [ ] **Step 4: Check forbidden tracked paths directly**

Run:

```bash
git ls-files | rg -n '(^internal/|^\.env(\.|$)|node_modules|receipt|invoice|\.webm$|\.mp4$|demo_captures|future_concepts|^\.autonomous/|^\.claude/|^progress/|^proposals/)'
```

Expected: no output.

- [ ] **Step 5: Check status and commit if needed**

Run:

```bash
git status --short
```

Expected: clean status. If validation created cache artifacts, remove or ignore
only those artifacts, rerun `git status --short`, then commit any necessary
ignore-only fix with:

```bash
git add .gitignore
git commit -m "chore: ignore validation artifacts"
```

- [ ] **Step 6: Prepare push/PR summary**

Collect:

```bash
git log --oneline origin/main..HEAD
git diff --stat origin/main..HEAD
```

Expected: summary clearly separates hardening commits, public docs commits,
artifact removal commits, and GitHub hygiene commits.

---

### Task 10: Post-Merge Branch Cleanup Owner Actions

**Files:**
- No source modifications.

- [ ] **Step 1: Confirm branch cleanup runbook exists**

Run:

```bash
test -f docs/github/BRANCH_CLEANUP_RUNBOOK.md
```

Expected: command exits `0`.

- [ ] **Step 2: After merge, fetch and inspect remote branches**

Run after the public cleanup branch is merged:

```bash
git fetch --all --prune
git ls-remote --heads origin
```

Expected: branch list includes `main` and any remaining stale candidates.

- [ ] **Step 3: Delete only approved stale branches**

Run only after confirming no open PR references the branch:

```bash
git push origin --delete codex-chimera-validation-fixes-20260424
git push origin --delete codex/student-dgx-runtime-profiles
```

Expected: GitHub removes the stale remote branches.

- [ ] **Step 4: Tag legacy master before any master deletion**

Run only with repository owner approval:

```bash
git fetch origin master
git tag legacy-master-20260505 origin/master
git push origin legacy-master-20260505
```

Expected: legacy `master` state is preserved by tag.

Do not delete `master` until GitHub confirms default branch is `main` and no
automation references `master`.
