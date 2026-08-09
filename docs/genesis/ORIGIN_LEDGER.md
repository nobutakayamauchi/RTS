# RTS Public Origin Ledger

This ledger exists to make RTS chronology easy to verify without relying on retrospective claims.

## Rule

For major RTS concepts, record the earliest repository evidence that can be publicly verified from GitHub commits or pull requests.

The ledger is evidence-first:

- GitHub history is the source of chronology;
- entries should link to concrete commits or pull requests;
- later summaries do not replace earlier evidence;
- similarity alone is not evidence of copying;
- independently developed similar ideas remain independent unless evidence shows otherwise.

## Current verified milestones

### Evidence-report and governed development line

Public repository history before August 2026 records deterministic evidence packages, fail-closed validation, governance gates, privacy hardening, public-candidate discovery, execution authorization, and product-readiness work.

### Deployment Identity / runtime debugging evidence pipeline

PR #299, opened 2026-08-07, records the invariant:

> Deployment Identity MUST be established before runtime implementation classification.

It also records the pipeline:

Observation → Deployment Identity Probe → Runtime Debug Gate → Runtime Evidence Correlation → Runtime Code Mapping Gate → Root Cause Claim Gate → Deployment Re-Identity → Retest / Regression Gate.

### Flight Recorder / Repair Patch / post-2026-07-26 FREEZER intake

PR #300, opened 2026-08-09, publicly records candidates including:

- RTS Flight Recorder;
- Repair Patch Generation Mechanism;
- Deployment Identity Layer;
- Governed Web Intake / Acquisition Layer;
- Limit Over / Quarantine / Safe Release Policy.

## Maintenance

When a major concept is adopted, add its earliest verifiable public evidence here. Prefer exact PR/commit links and dates over narrative claims.

This ledger documents chronology and provenance. It does not claim that similar later work by another party was copied from RTS unless separate evidence establishes that fact.
