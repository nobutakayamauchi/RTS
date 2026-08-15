# BridgePatch Launch Observation

Status: `ACTIVE / MINIMAL FUNNEL / NO NEW LARGE DEVELOPMENT`

## Purpose

Observe whether the live BridgePatch offer reaches a real prospect and where friction appears before building more infrastructure.

## Minimal funnel

Track only these five events:

1. `SEEN` — external post was actually published and can be viewed.
2. `VISIT` — a prospect reaches the BridgePatch sales page or clearly references it.
3. `INQUIRY` — a real prospect sends a BridgePatch inquiry.
4. `FIT_CHECK` — the four-question free fit check is answered far enough to classify FIT / NEED_MORE_INFO / OUT_OF_SCOPE.
5. `PAID_SPEC` — the JPY 10,000 BridgePatch implementation design specification is purchased.

Do not build an analytics application just to count these events.

## Record shape

For each meaningful event, retain only what is needed:

```text
date/time
channel/source: X / note / GitHub / direct / unknown
event: SEEN / VISIT / INQUIRY / FIT_CHECK / PAID_SPEC
reference: URL, message/thread reference, or Stripe payment reference when available
next action
notes: short, factual, no unnecessary personal data
```

If a metric cannot be directly observed, record `UNKNOWN`; do not infer a number.

## Priority rule

A qualified inbound prospect overrides unrelated feature work.

```text
QUALIFIED INBOUND > NEW FEATURE WORK
```

Once an inquiry arrives:

```text
INQUIRY
-> use Gmail BridgePatch intake template
-> ask the four fit-check questions
-> FIT / NEED_MORE_INFO / OUT_OF_SCOPE
-> if FIT and useful: offer JPY 10,000 design specification
-> after payment: follow INQUIRY_FLOW.md and prepayment/start-notice rules
```

Do not start Real World Roguelike or another large product while a qualified BridgePatch inbound needs action.

## What not to optimize yet

Until real traffic or inquiry evidence exists, do not add:

- custom analytics backend;
- CRM application;
- automated DM/outreach;
- automatic social publishing;
- attribution model beyond the five events;
- new BridgePatch product tiers;
- unrelated large development.

First learn from actual publication, inquiry, fit-check, payment and delivery friction.
