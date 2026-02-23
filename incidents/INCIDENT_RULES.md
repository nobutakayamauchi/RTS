# RTS Incident Report --- Execution Audit Template v3

RTS records operational reality. Execution failure becomes operational
memory.

------------------------------------------------------------------------

## Metadata Header (Required)

incident_id: INC_YYYYMMDD_HHMM\
system:\
severity: S0 / S1 / S2 / S3 / S4\
status: OPEN / MITIGATED / CLOSED\
operator:\
lifecycle_state: INCIDENT / INVESTIGATION / INTERVENTION / RECOVERY /
KNOWLEDGE

detection_source: operator / automation / public_report / vendor_notice

environment: device: interface: workflow:

model: provider: name: version:

timeline: detected: investigation_started: mitigation_started:
recovered:

reproducible: yes / partial / no

hypothesis_confidence: low / medium / high

evidence: - URL_REQUIRED

------------------------------------------------------------------------

## Symptom

Observed behaviour only. Facts. Avoid speculation.

------------------------------------------------------------------------

## Reproduction Steps (Required)

Minimum:

1.  Workflow length
2.  Interaction type
3.  Triggering actions

If unknown:

"Reproduction unknown."

------------------------------------------------------------------------

## Operational Impact

Describe operator consequences.

Examples:

-   workflow delay
-   manual rebuild required
-   research interruption

------------------------------------------------------------------------

## Hypothesis

Initial explanation based on available evidence.

Avoid definitive claims.

------------------------------------------------------------------------

## Validation Method

How hypothesis is tested.

Examples:

-   reproduction experiment
-   vendor confirmation
-   controlled retry

------------------------------------------------------------------------

## Confirmed Cause

Root cause verified through evidence.

If unknown:

"Unconfirmed."

------------------------------------------------------------------------

## RTS Intervention

Operator response actions.

Examples:

-   execution logging initiated
-   workflow isolation
-   rollback

------------------------------------------------------------------------

## Recovery

Mitigation outcome.

Examples:

-   manual audit completed
-   workflow rebuilt

------------------------------------------------------------------------

## Lessons Learned

Operational learning extracted.

------------------------------------------------------------------------

## Evidence (Required)

Must include at least one:

-   Public discussion
-   Vendor statement
-   GitHub issue
-   Reproducible log

Links required.

------------------------------------------------------------------------

## Lifecycle Reference

INCIDENT â INVESTIGATION â INTERVENTION â RECOVERY â KNOWLEDGE

RTS preserves execution history as operational infrastructure.
