# GitHub Notes Review - 2026-05-11

Status: PUBLIC REPOSITORY MAINTENANCE NOTE - NOT GRANT EVIDENCE.

This file records the GitHub-facing maintenance notes reviewed on 11 May 2026
and the repository changes made in response. It is intended to make the public
repo easier to maintain and to keep the Phase 1 close-out branch understandable
for reviewers.

## 1. Notes Reviewed

The following GitHub-visible notes were reviewed:

- GitHub Actions warning that several workflows used Node.js 20-based action
  versions.
- GitHub Actions checkout warning caused by a tracked `integrations/bettafish`
  gitlink without a matching `.gitmodules` entry.
- Open Dependabot pull requests for vulnerable dependency updates.
- Open Dependabot alerts reported by the repository dependency graph.
- Branch-protection warning emitted during an administrator direct push.

## 2. Resolved In This Repository Pass

### GitHub Actions Node.js warning

Action versions were updated across `.github/workflows/`:

- `actions/checkout@v4` -> `actions/checkout@v6.0.2`
- `actions/setup-python@v5` -> `actions/setup-python@v6.2.0`
- `actions/cache@v4` -> `actions/cache@v5.0.5`

Expected effect:

- Removes the deprecated Node.js 20 action warning once the updated workflows
  run on GitHub.

### Broken `integrations/bettafish` gitlink

The public index previously tracked `integrations/bettafish` as a submodule-like
gitlink but there was no `.gitmodules` file. GitHub checkout could complete the
main jobs, but post-job checkout cleanup emitted:

- `fatal: No url found for submodule path 'integrations/bettafish' in .gitmodules`

Resolution:

- Removed `integrations/bettafish` from the public git index.
- Added `integrations/bettafish/` to `.gitignore`.
- Left the local folder untouched so any private or local integration checkout
  remains available on this machine.

Expected effect:

- Removes the GitHub checkout submodule warning without publishing or deleting
  local integration material.

### Dependabot dependency alerts

Dependency manifests were updated for the packages GitHub flagged:

| Area | File | Change |
| --- | --- | --- |
| Sentiment agent | `services/sentiment-agent/requirements.txt` | `transformers` to `5.0.0rc3`, `torch` to `2.8.0`, `pytest` to `9.0.3` |
| Educational platform | `services/educational-platform/requirements.txt` | `python-multipart` to `0.0.27`, `python-dotenv` to `1.2.2`, `pytest` to `9.0.3` |
| Dashboard | `services/dashboard/requirements.txt` | `jinja2` to `3.1.6`, `pytest` to `9.0.3` |
| Health aggregator | `services/health-aggregator/requirements.txt` | `pytest` to `9.0.3` |
| Operator console | `services/operator-console/requirements.txt` | `pytest` to `9.0.3`, `python-multipart` lower bound to `0.0.27` |
| Nemoclaw orchestrator | `services/nemoclaw-orchestrator/requirements.txt` | `python-multipart` lower bound to `0.0.27`, `python-dotenv` lower bound to `1.2.2` |
| Claude orchestrator | `services/claude-orchestrator/go.mod` | `golang.org/x/crypto` to `0.45.0`, `golang.org/x/net` to `0.47.0`, `google.golang.org/protobuf` to `1.33.0` |

The Go security updates required the Claude orchestrator module to move from
`go 1.21` to `go 1.24.0`, because the patched `golang.org/x/crypto` release
requires Go 1.24 or newer.

Expected effect:

- GitHub Dependabot alerts should reduce after the dependency graph refreshes.
- Open Dependabot PRs that only performed these version bumps should become
  superseded by the main branch once these changes are pushed and verified.

## 3. Still Requires GitHub Refresh Or Human Review

### Dependency graph refresh

GitHub may not dismiss vulnerability alerts immediately after the commit lands.
Re-check the repository security tab after the next dependency graph refresh.

### Open Dependabot PRs

The following Dependabot PRs were reviewed as part of this pass:

- `#15` pytest update in `services/sentiment-agent`
- `#17` transformers update in `services/sentiment-agent`
- `#18` torch update in `services/sentiment-agent`

If the main branch contains the same or newer dependency updates and checks pass,
these PRs can be closed as superseded.

### Branch-protection bypass note

GitHub reported that the latest administrator push bypassed branch protection.
That is a repository governance/admin setting, not a source-file defect.

Recommended owner decision:

- Use pull requests for future public changes where practical.
- If direct administrator pushes should never bypass checks, update GitHub
  branch protection or ruleset settings in the repository admin UI.

## 4. Close-Out Relevance

These changes improve the public repository hygiene for the narrowed Phase 1
claim. They do not create grant evidence, financial evidence, approval evidence,
student participation evidence, or public-performance evidence.

The close-out submission still needs human-provided private evidence and human
review before submission.

## 5. Validation Run Before Commit

The following local checks were run after the GitHub-note fixes:

| Command | Result |
| --- | --- |
| `git diff --check` | Passed |
| `python3 scripts/privacy_preflight.py` | Passed |
| `python3 scripts/scan_for_secrets.py --include-untracked --fail-on-findings` | Passed: no secret-like findings |
| `python3 scripts/scan_for_overclaims.py --include-untracked --fail-on-review` | Passed: guarded / Phase 2 findings only |
| `python3 scripts/check_markdown_links.py` | Passed |
| `python3 scripts/run_phase1_demo.py` | Passed and wrote an ignored local run log under `outputs/run_logs/` |
| `python3 test_chimera_smoke.py` | Passed: 6 passed, 0 failed |
| `python3 -m pytest -p no:cacheprovider tests/unit/test_chimera_core.py tests/unit/test_chimera_web_contract.py tests/unit/test_public_repo_cleanup_contract.py tests/unit/test_privacy_preflight.py -q` | Passed: 45 passed |
| `env GOSUMDB=sum.golang.org <local-go> test ./...` in `services/claude-orchestrator` | Passed |

The demo run log was not committed because generated logs are intentionally
kept out of the public repository.
