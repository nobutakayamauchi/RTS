# CURRENT MINIMAL CORE (Snapshot)

## Purpose
This document is a current-state structural summary of the minimal RTS core and connected operator-side structure. It is not a final design.

## RTS Core
The current minimal RTS core is centered on a shared execution/evidence foundation:
- `schemas/execution_record.schema.yaml`
- `schemas/evidence_ref.schema.yaml`
- `docs/overview/EXECUTION_AND_EVIDENCE.md`

## Skill Set
The current minimal operator-side structure includes 10 skills:
- `weekly_dev_report`
- `monthly_revenue_summary`
- `client_payment_status_report`
- `issue_to_fix_pr`
- `failed_build_to_patch_plan`
- `sentry_error_to_root_cause_report`
- `notion_knowledge_retrieval`
- `slack_thread_summary`
- `important_mail_triage`
- `site_price_watch_with_screenshot`

## Pack Set
The current pack set includes 5 packs:
- `dev_pack`
- `knowledge_pack`
- `mail_pack`
- `revenue_pack`
- `research_pack`

## Drive
Current drive:
- `hermes_drive`

## Structural Meaning
The current minimal RTS core now supports a multi-skill, multi-pack operator structure through a shared execution record model and evidence reference layer.

## Boundary
This document is only a structural inventory and does not define runtime logic, full evidence linkage, checkpointing, or full orchestration behavior.
