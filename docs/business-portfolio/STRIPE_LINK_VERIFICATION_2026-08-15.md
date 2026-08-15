# Stripe Link Verification — 2026-08-15

Status: `HUMAN_SCREEN_VERIFIED / CONFIGURATION_REUSE_POSSIBLE`

## BridgePatch candidate

Human screenshots of the RS AI Stripe Dashboard verified an active JPY 10,000 Payment Link created on 2026-03-18 for:

`新規案件 初動フローチャート策定`

Observed configuration:

- amount: JPY 10,000
- quantity: 1
- adjustable quantity: disabled
- active: yes
- customer email appears on checkout
- address collection: disabled
- phone collection: disabled
- individual-name collection: disabled
- business-name collection: disabled
- terms agreement collection: disabled
- completion page: custom message
- metadata: none

### Decision

Do **not** create a new JPY 10,000 Payment Link yet.

This existing link is a viable reuse candidate, but it does not yet satisfy the current BridgePatch customer-information contract. Before using it publicly, edit/reconfigure one retained JPY 10,000 link so that the checkout and product copy match BridgePatch.

Required BridgePatch adjustments:

1. product/display name -> `BridgePatch 暫定ツール実装設計書`
2. preserve JPY 10,000 / one-time / quantity 1
3. collect individual full name
4. collect business name when applicable
5. retain email collection
6. replace the old completion message with the current BridgePatch follow-up message or approved redirect
7. re-run the checkout smoke test before public use

The exact public `buy.stripe.com/...` URL should be copied as text after final edit; screenshots showing truncated URLs are not treated as the authoritative stored URL.

## RTS AXIS / Breakpoint Consulting

Human screenshots also verified an active JPY 49,500 generic Payment Link named:

`Breakpoint Consulting`

Observed:

- amount: JPY 49,500
- quantity: 1
- adjustable quantity: disabled
- active: yes
- checkout preview includes email and individual name
- terms agreement collection: disabled
- completion page: default

### Decision

The existence of this generic JPY 49,500 Payment Link proves that a direct-payment link was previously configured, but it does **not** replace the current RTS AXIS sales boundary.

RTS AXIS remains:

`inquiry -> free fit check -> written scope/terms -> explicit consent -> customer-specific Stripe invoice -> payment -> work`

Therefore the Breakpoint Consulting Payment Link is **not** the AXIS public CTA for the current v0 sales flow. Do not publish it as an AXIS buy-now link without a separate explicit redesign decision.

## Shared contact decision

Human confirmed the public contact email for both BridgePatch and RTS AXIS:

`yamauchi.rts.office@gmail.com`

This value is now treated as fixed for the active launch-preparation cycle.
