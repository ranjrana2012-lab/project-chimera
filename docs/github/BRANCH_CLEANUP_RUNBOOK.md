# Branch Cleanup Runbook

Run this after the public cleanup branch is merged.

## Safety Checks

```bash
git fetch --all --prune
git ls-remote --heads origin
```

## Candidate Branches

- origin/codex-chimera-validation-fixes-20260424
- origin/codex/student-dgx-runtime-profiles
- origin/master

## Delete Reviewed Cleanup Branches

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
