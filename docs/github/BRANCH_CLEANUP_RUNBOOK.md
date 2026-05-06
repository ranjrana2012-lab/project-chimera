# Branch Cleanup Runbook

Run this after the public cleanup branch is merged.

Status: completed on 2026-05-06.

## Safety Checks

```bash
git fetch --all --prune
git ls-remote --heads origin
```

For each candidate branch, confirm:

- No open pull request targets or uses the branch.
- No unique commits need to be preserved.
- The repository owner agrees to deletion or legacy tagging.

## Candidate Branches

- origin/codex-chimera-validation-fixes-20260424
- origin/codex/student-dgx-runtime-profiles
- origin/master

## Completed Remote State

- `codex/student-dgx-runtime-profiles` was fully contained in `main` and was
  deleted.
- `codex-chimera-validation-fixes-20260424` had two unique commits; it was
  preserved as `archive/codex-chimera-validation-fixes-20260424` and the stale
  branch name was deleted.
- `master` had unrelated legacy history; it was preserved as
  `legacy/master-20260506` and the confusing `master` branch name was deleted.

## Delete Reviewed Cleanup Branches

Only run these after the safety checks pass:

```bash
git push origin --delete codex-chimera-validation-fixes-20260424
git push origin --delete codex/student-dgx-runtime-profiles
```

## Preserve Legacy `master`

Tag `master` before any deletion:

```bash
git fetch origin master
git tag legacy-master-20260505 origin/master
git push origin legacy-master-20260505
```

Do not delete `master` until the GitHub default branch is `main` and no automation references `master`.
