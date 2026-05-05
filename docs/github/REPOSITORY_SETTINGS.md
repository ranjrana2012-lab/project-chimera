# GitHub Repository Settings

These settings require repository owner access. They are not completed by file edits alone.

## Branch Protection For `main`

- Require a pull request before merge.
- Require one approving review.
- Require status checks to pass before merge.
- Require the active CI workflow as a status check.
- Dismiss stale approvals when new commits are pushed.
- Restrict force pushes.
- Restrict deletions.

## Repository Hygiene

- Enable secret scanning.
- Enable Dependabot alerts.
- Enable automatic deletion of merged branches.
- Add description: `AI-powered live theatre research platform with a local adaptive Phase 1 demonstrator`
- Add topics: `ai`, `theatre`, `adaptive-ai`, `fastapi`, `docker`, `research`

## Releases

- Use `CHANGELOG.md` as the release source.
- Publish GitHub Releases for stable tags.
- Keep `v1.0.0-phase1` as the Phase 1 public milestone unless a newer reviewed release supersedes it.
