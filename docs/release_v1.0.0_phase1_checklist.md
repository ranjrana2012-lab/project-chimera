# v1.0.0 Phase 1 Public Release Checklist

Status: HUMAN ACTION REQUIRED.

This checklist prepares a public Phase 1 release. It is not a release tag,
approval record, or submission evidence.

## Repository Gate

- [ ] `README.md` frames the project as a Phase 1 local adaptive AI
      demonstrator.
- [ ] `LICENSE` is present and human-confirmed as appropriate for release.
- [ ] `QUICKSTART.md` runs on the Student / Laptop route.
- [ ] `docs/closeout/` and `chimera_closeout_pack/` distinguish templates from
      evidence.
- [ ] No private grant records, invoices, receipts, bank statements, generated
      recordings, generated logs, participant data, tokens, or `.env` files are
      tracked.

## Claim Gate

- [ ] No public show, livestream, 40-student, production deployment, validated
      accessibility, two-DGX, or partner-approval claim appears without direct
      evidence.
- [ ] Advanced DGX/Kimi material is labelled as advanced or maintainer-only.
- [ ] The AHRC/BCU acknowledgement uses approved wording supplied by a human.

## Demonstrator Gate

- [ ] `python3 services/operator-console/chimera_core.py demo` has been run.
- [ ] `python3 scripts/run_phase1_demo.py` has generated a real local log.
- [ ] `python3 test_chimera_smoke.py` has passed.
- [ ] `python3 scripts/privacy_preflight.py` has passed.
- [ ] A human has recorded the 3-5 minute demo video and stored it privately.

## Release Gate

- [ ] `git status` is clean.
- [ ] Human reviewer has checked all close-out and release wording.
- [ ] Human creates or pushes tag `v1.0.0-Phase1` or agreed successor tag.
- [ ] Release notes state that the release is a Phase 1 demonstrator, not a
      completed production/live-performance system.
