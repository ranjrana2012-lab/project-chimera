# Project Chimera Phase 1 Demo Video Recording Checklist

Status: HUMAN ACTION REQUIRED.

Use this checklist for a 3-5 minute narrated screen recording that supports the
Phase 1 local-first adaptive AI demonstrator claim. Do not present the recording
as evidence of a public show, livestream, formal accessibility testing, audience
impact, partner approval, or financial spend.

## Recording Content

- Show the public repository root and the Phase 1 framing in `README.md`.
- Show the exact command used to run the demo.
- Run the local CLI demo or `scripts/run_phase1_demo.py`.
- Show these example inputs if they route correctly in the current build:
  - `I am sad`
  - `I feel excited and ready`
  - `I am confused and overwhelmed`
  - `This is intense but inspiring`
- Show the selected adaptive strategy for each input.
- Show the generated local run log path under `outputs/run_logs/`.
- If the demo uses local inference or a heuristic fallback, describe that
  accurately. Do not imply cloud APIs were absent unless the recorded run proves
  it.
- Show `scripts/privacy_preflight.py` passing before submission.

## Narration Guardrails: Claims To Avoid

Use cautious language:

- "Phase 1 local adaptive AI demonstrator"
- "controlled demo"
- "local-first adaptive AI framework"
- "designed for future audience input"

Avoid:

- Do not claim: "public show delivered".
- Do not claim: "livestream delivered".
- Do not claim: "40 students upskilled".
- Do not claim: "validated accessibility testing".
- Do not claim: "BSL/avatar delivery completed".
- Do not claim: "production-ready deployment".

## Evidence Handling

Store the final recording privately. Do not commit MP4, MOV, WEBM, raw captures,
generated screenshots, logs, participant data, invoices, bank statements, tokens,
or private grant records to public git.
