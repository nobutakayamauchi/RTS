# Event Assist — Thin State Binding

Status: `METEOR_CANDIDATE / CI_REQUIRED`

Event Assist is **not** an RTS-owned life-management platform.

The surviving custom responsibility is one pure state binder/validator:

`event_state.py`

Everything else remains external or already adopted:

- interpretation/classification: external AI/tool;
- official-source retrieval: external browser/search/official portal;
- scheduling/notifications: external/native scheduler;
- evidence payloads, integrity, encryption and custody: existing Security Intake / Cloud Custody contracts;
- fresh recovery/failure domains: existing Continuity contract;
- documents/forms: external document tooling;
- submission/disclosure/promotion: separately authorized human/external action.

## `/goal`

Validate one typed event case:

```bash
python3 event_state.py goal fixtures/case_b_childbirth_current_sources.json \
  --at 2026-08-13T01:00:00Z
```

Output is deterministic for the same case and evaluation time.

The binder fails closed on material structural contradictions and reports visible blocking states for evidence gaps, stale/broken watches, overdue deadlines, missing required authority, event uncertainty and explicit unknowns.

## Current-source binding

A VERIFIED legal/deadline pin or ready-state document requires a current official source **and** a decision-time observed artifact reference + SHA-256. The artifact itself remains in Git/Custody/Continuity; Event Assist only binds it.

A news/social signal can trigger a candidate recheck but cannot become a VERIFIED legal/procedure conclusion by itself.

## Deliberate non-features

No network client, crawler, law database, scheduler, watcher daemon, database, evidence store, crypto, cloud transport, notification sender, document renderer, or submission executor is implemented here.

## Tests

```bash
python3 -m unittest -v test_event_state.py test_meteor_event_state.py
```

The PHOENIX creator-absent regeneration test is separate under `thin-rts/phoenix/`.
