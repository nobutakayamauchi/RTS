# BridgePatch Inbound Inquiry Flow

Status: `ACTIVE SALES OPERATING FLOW / NO NEW APP REQUIRED`

Public contact:

`yamauchi.rts.office@gmail.com`

Primary sales page:

`https://nobutakayamauchi.github.io/RTS/bridgepatch/`

## Goal

Turn a vague pain report into one of three safe outcomes with as little friction as possible:

```text
INQUIRY
-> FREE FIT CHECK
-> FIT / NEED_MORE_INFO / OUT_OF_SCOPE
-> if useful: JPY 10,000 implementation design spec
-> if implementation is later agreed: bounded simple-tool offer
```

Do not build a paid-intake application for this flow.

## First reply: ask only what is needed

Ask the prospect to reply with these four items:

1. **いま何を手作業でしていますか？**
2. **どのくらいの頻度・時間がかかっていますか？**
3. **最終的に何が出れば助かりますか？**
4. **間違った場合、どの程度の影響がありますか？**

Optional only when necessary:

- sample input/output with secrets removed;
- current tool names;
- deadline;
- whether personal, medical, payment, credential, or other sensitive data is involved.

Never request passwords, API secrets, private keys, card security codes, or unnecessary identity/health records by email.

## Free fit-check classification

### FIT

Use when all of the following are reasonably true:

- one painful workflow can be isolated;
- one main input / process / output can be described;
- a human can review the result when needed;
- failure does not directly create severe or irreversible harm;
- the work can fall back to the existing manual process.

Reply with a short description of the candidate boundary. Do not give away a full implementation design during the free check.

If the customer wants the boundary, workflow, exclusions, safety conditions, acceptance criteria, and expected implementation range documented, route to the JPY 10,000 design spec.

### NEED_MORE_INFO

Ask only for the missing fact that prevents a fit decision. Do not start broad requirements discovery for free.

### OUT_OF_SCOPE / REVIEW_REQUIRED

Do not accept as a normal simple-tool engagement when the requested flow includes severe-risk or materially different scope, including examples such as:

- medical or care decisions;
- final payroll/payment decisions;
- life-safety decisions;
- credential or secret handling as a normal workflow;
- large-scale sensitive-data processing;
- high-availability / 24-hour critical operation;
- illegal or rights-infringing use.

## JPY 10,000 design-spec route

Canonical Payment Link:

`https://buy.stripe.com/5kQ3cxb5SaTz0LI8jV3Nm0f`

Product:

`BridgePatch 暫定ツール実装設計書`

The product is a design/specification deliverable. Tool implementation itself is not included.

After payment:

1. confirm customer name / business name / email captured by Stripe;
2. send the required-information request;
3. send any legally required prepayment notice using `PREPAYMENT_NOTICE_TEMPLATE.md`;
4. send a clear start notice before treating the work as started;
5. deliver after required information is received, normally within the published 5-business-day boundary;
6. retain evidence of what was agreed and delivered.

## Simple-tool route

Do not take JPY 50,000 merely because the customer asks for implementation.

Before starting, confirm in writing:

- exact target workflow;
- main input / process / output;
- exclusions;
- safety / human-review conditions;
- acceptance conditions;
- total price;
- delivery timing;
- cancellation/refund conditions;
- data/services involved.

Then use the individually agreed payment method and begin only after the agreed payment condition is met.

## Operating rule

A real inbound inquiry becomes priority over unrelated new development.

```text
QUALIFIED INBOUND > NEW FEATURE WORK
```

Do not expand BridgePatch infrastructure merely because there is no customer yet. First measure actual inquiry, fit-check, paid-spec, and delivery friction.
