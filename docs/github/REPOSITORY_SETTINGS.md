# GitHub Repository Settings

These settings require repository owner access. They are not completed by file edits alone.

Status: applied on 2026-05-06 for the public Phase 1 baseline.

## Branch Protection For `main`

- Require a pull request before merge.
- Require one approving review.
- Require status checks to pass before merge.
- Require `test` and `check-links` as status checks.
- Dismiss stale approvals when new commits are pushed.
- Restrict force pushes.
- Restrict deletions.
- Require conversation resolution.

## Repository Hygiene

- Secret scanning is enabled.
- Automatic deletion of merged branches is enabled.
- Wiki is disabled; repository docs are kept in git.
- Add description: `AI-powered live theatre research platform with a Phase 1 local adaptive AI demonstrator.`
- Add topics: `adaptive-ai`, `ai`, `education`, `fastapi`, `live-performance`,
  `microservices`, `python`, `research`, `sentiment-analysis`, `theatre`

## Releases

- Use `CHANGELOG.md` as the release source.
- Publish GitHub Releases for reviewed public tags.
- Use `v1.0.1-phase1` for the cleaned public Phase 1 baseline.
