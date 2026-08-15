# /goal — Revenue Priority 2026-08-15

Date: **2026-08-15 JST**

Status: `SALES_BLOCKERS_FIRST / POST_ADAPTER_NEXT / LARGE_VENTURE_PRESERVED`

## Goal

Preserve the human-important business outcome:

> Convert the development assets that already exist into revenue with the least additional build work, then use that path to fund and expose higher-value products without losing the strongest long-horizon venture candidate.

The immediate target order is frozen as:

1. Verify and classify BridgePatch sales blockers.
2. Verify and classify RTS AXIS sales blockers.
3. Start Post Adapter v0 immediately after the blocker review is complete.
4. Preserve Real World Roguelike as the #1 large-venture candidate, but do not start implementation now.

## Evidence refresh

### BridgePatch

Existing retained material already contains:

- static sales LP;
- terms/privacy/tokusho templates;
- order-confirmation display plan;
- sales/contract/checklist documents;
- a configuration boundary for real URLs and seller information;
- free fit check;
- JPY 10,000 portable implementation-spec product;
- JPY 50,000 simple-tool offer.

Therefore the current problem is **not lack of product design**. The remaining work is launch configuration and launch verification.

Known launch fields include:

- free consultation URL;
- JPY 10,000 Stripe Payment Link;
- contact email;
- seller/operator identity;
- address/phone disclosure method;
- jurisdiction display;
- public hosting target;
- final cross-page/link check.

The paid intake form is **not allowed to become a new prerequisite by default**. Existing material already defines an email-follow-up completion message when no paid-intake redirect exists.

### RTS AXIS

The approved sales boundary already exists:

`note sales page -> Gmail inquiry -> free fit check -> written scope/terms -> explicit consent -> customer-specific Stripe invoice -> payment confirmation -> paid work`

The JPY 49,500 price and 100% prepayment boundary survive.

Remaining blockers are launch/operations work rather than a reason to redesign the product:

- decide the public display method for address and phone;
- finalize the public inquiry address;
- create/finalize the note sales page;
- finalize the Gmail -> consent -> Stripe invoice customer path;
- cross-check customer documents, Stripe wording, and public-page wording;
- re-run the remaining public-sale gates;
- obtain explicit human `PUBLIC_SALE_APPROVED` before actual publication or billing.

A shared instant-buy payment link is not part of AXIS v0. Billing remains customer-specific and occurs only after written consent.

### Post Adapter discovery

Direct automatic publication is technically possible for some platforms, but it is not required to prove the useful core:

- X provides authenticated post-creation APIs.
- Instagram provides content-publishing APIs for supported professional accounts.
- note currently states that it does not provide an official public API.

Therefore cross-platform API publishing, OAuth/account storage, token refresh, scheduling, and platform-specific operational failure handling are rejected from v0.

## Raison d'être destroy result

Killed for the current cycle:

- BridgePatch redesign;
- new BridgePatch service tiers before first sale;
- RTS AXIS engine redesign;
- additional AXIS analysis features before public-sale readiness;
- building a paid-intake application only because a redirect placeholder exists;
- Post Adapter auto-posting;
- Post Adapter credential vault;
- Post Adapter scheduling;
- Post Adapter engagement analytics;
- Post Adapter multi-user SaaS;
- Real World Roguelike implementation now;
- unrelated RTS/Ultimate Loop expansion that does not unblock the active revenue path.

## Surviving irreducible work

### Work Package A — BridgePatch blocker matrix

Classify every launch field as one of:

- `DONE`
- `HUMAN_INPUT_REQUIRED`
- `EXTERNAL_ACCOUNT_ACTION_REQUIRED`
- `LEGAL_REVIEW_REQUIRED`
- `TECHNICAL_FIX_REQUIRED`
- `VERIFICATION_REQUIRED`

Output one next action per unresolved blocker. Do not turn an external-account or legal decision into a software project.

### Work Package B — RTS AXIS blocker matrix

Use the same blocker classes and preserve these hard boundaries:

- free fit check contains no paid analysis deliverable;
- explicit written consent precedes billing;
- customer-specific Stripe invoice;
- work starts after payment;
- no public sale, live invoice, Ready conversion, or merge without the existing human gate.

### Work Package C — Post Adapter v0

Start only after Work Packages A and B have produced complete blocker matrices.

Post Adapter v0 is a **human-reviewed content transformation layer**, not an autonomous publishing bot.

See `POST_ADAPTER_V0_SPEC.md`.

## Build verdict

`DO SALES-BLOCKER CLASSIFICATION NOW`

`DO NOT REDESIGN BRIDGEPATCH OR AXIS`

`BUILD POST ADAPTER V0 NEXT`

`PRESERVE REAL WORLD ROGUELIKE AS LARGE-VENTURE PRIORITY #1`

`DO NOT START REAL WORLD ROGUELIKE IMPLEMENTATION IN THIS CYCLE`

## Completion gate for this /goal

This /goal is satisfied when:

1. BridgePatch has a complete blocker matrix with exactly one next action per unresolved blocker.
2. RTS AXIS has a complete blocker matrix with exactly one next action per unresolved blocker.
3. Post Adapter v0 scope is frozen with direct posting explicitly out of scope.
4. The portfolio records Real World Roguelike as `LARGE_VENTURE_PRIORITY = 1`, `FROZEN`, and `NOT_SELECTED`.
5. No public sale, live customer billing, or external post is performed as a side effect of this planning record.
