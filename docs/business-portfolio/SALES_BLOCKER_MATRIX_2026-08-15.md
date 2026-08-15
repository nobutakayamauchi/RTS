# Sales Blocker Matrix — 2026-08-15

Status: `BRIDGEPATCH_LIVE / AXIS_LIVE / POST_ADAPTER_NEXT`

This matrix supersedes earlier handoff-based and prelaunch assumptions with the current repository, Stripe, GitHub Pages, and release evidence.

# A. BridgePatch

| ID | Blocker / requirement | Status | Current evidence | Next action |
|---|---|---|---|---|
| BP-01 | Product boundary and offer ladder | `DONE` | Free fit check, JPY 10,000 portable implementation spec, JPY 50,000 simple tool remain the frozen offer | No redesign |
| BP-02 | Seller/operator identity | `DONE` | `山内 延天（屋号：RS AI）` / operator `山内 延天` | Preserve |
| BP-03 | Public contact email | `DONE` | `yamauchi.rts.office@gmail.com` is the canonical public contact | Preserve |
| BP-04 | Free consultation route | `DONE` | Production config uses the canonical mailto route | Preserve |
| BP-05 | Dedicated JPY 10,000 Price | `DONE` | `price_1U4ewGPYxtfxmKGliOKXtIP1`, JPY 10,000, one-time, tax behavior inclusive | Preserve |
| BP-06 | Dedicated Payment Link | `DONE` | `plink_1U4ewTPYxtfxmKGlnNEYk9Bs` / `https://buy.stripe.com/5kQ3cxb5SaTz0LI8jV3Nm0f`, live and active | Preserve |
| BP-07 | Payment line-item identity | `DONE` | Stripe line-item smoke returns `BridgePatch 暫定ツール実装設計書`, quantity 1, adjustable quantity false, total JPY 10,000 | Preserve |
| BP-08 | Retire incorrect reused legacy link | `DONE` | Legacy `plink_1TCBEnPYxtfxmKGlmuK4Cwqe` set inactive after the stale line-item description was discovered | Do not reactivate |
| BP-09 | Address/phone disclosure method | `DONE` | Disclosure-on-request path staged; verified non-public seller address and reachable phone exist outside public repository | Re-review only if law/operation changes |
| BP-10 | Hosting / production URL | `DONE` | GitHub Pages uses `main` root; production route `https://nobutakayamauchi.github.io/RTS/bridgepatch/` | Preserve |
| BP-11 | Production config / public documents | `DONE` | LP, terms, privacy, commercial disclosure, prepayment procedure and config are on `main` | Preserve |
| BP-12 | Checkout boundary text | `DONE` | Checkout states product boundary, delivery timing and cancellation/refund boundary; completion message points to public email | Preserve |
| BP-13 | Founder public-sale approval | `DONE` | Explicit `PUBLIC_SALE_APPROVED` received 2026-08-15 JST and recorded on PR #334 | Reapprove only on a material trigger |
| BP-14 | Initial Pages deployment | `DONE` | PR #334 merged; Pages build succeeded for commit `7bbbaf4180393e5dfdc4b3bc2e33a2ebedfc769b` | Superseded by payment-link hotfix |
| BP-15 | Payment-link v2 hotfix deployment | `DONE` | PR #335 merged; Pages build succeeded with no error for commit `fb66986ac60347134ace9f0597871f22ca27e748`; `main` config points to v2 URL | Preserve |

## BridgePatch current operating state

```text
PUBLIC_SALE_APPROVED: YES
PUBLIC_SALE_ACTIVE: YES
PAGES_BUILD: PASS
CANONICAL_PAYMENT_LINK: plink_1U4ewTPYxtfxmKGlnNEYk9Bs
CANONICAL_PAYMENT_URL: https://buy.stripe.com/5kQ3cxb5SaTz0LI8jV3Nm0f
CANONICAL_PRICE: price_1U4ewGPYxtfxmKGliOKXtIP1
LEGACY_PAYMENT_LINK: INACTIVE
ACTIVE_PAID_ENGAGEMENTS: not inferred from launch state
```

No additional BridgePatch product-development work is authorized merely because no customer has purchased yet.

# B. RTS AXIS

The earlier handoff used during the first blocker pass was stale. Current `nobutakayamauchi/RTS-minicompany` main establishes the later release state.

| ID | Requirement | Status | Current evidence | Next action |
|---|---|---|---|---|
| AX-01 | Product / JPY 49,500 / scope | `DONE` | Approved active service profile | Preserve |
| AX-02 | Public seller identity and customer surfaces | `DONE` | Gates A-H and final cross-surface comparison passed | Preserve |
| AX-03 | Explicit `PUBLIC_SALE_APPROVED` | `DONE` | Founder approval recorded 2026-07-23 12:33 JST; Gate I passed | Preserve until reapproval trigger |
| AX-04 | Repository release | `DONE` | PR #91 merged | No action |
| AX-05 | note sales page | `DONE` | Published article `n86c36f6a406c`; controlled public launch active | Keep live unless pause trigger occurs |
| AX-06 | Inquiry route | `DONE` | Inbound inquiry route open and ready for fit checks | Handle inbound as it arrives |
| AX-07 | Gmail / written-consent / customer-specific Stripe invoice flow | `DONE` | Customer flow and safe pre-send invoice preview approved | Use only for a specific customer after written consent |
| AX-08 | Live invoice / paid work | `NOT_BLOCKING` | Customer-specific consent and payment gates remain operational boundaries, not product-launch blockers | Wait for qualifying customer |
| AX-09 | Initial capacity | `DONE` | Controlled launch cap is one simultaneous paid engagement | Do not exceed cap without separate review |

## RTS AXIS current operating state

```text
PUBLIC_SALE_APPROVED: YES
PR_RELEASE_COMPLETED: YES
NOTE_PAGE_PUBLISHED: YES
CONTROLLED_PUBLIC_LAUNCH_ACTIVE: YES
INBOUND_INQUIRY_ROUTE_OPEN: YES
READY_FOR_INBOUND_FIT_CHECKS: YES
ACTIVE_PAID_ENGAGEMENTS: 0
SIMULTANEOUS_PAID_ENGAGEMENT_CAP: 1
LIVE_CUSTOMER_INVOICE: CUSTOMER-SPECIFIC CONSENT GATE REQUIRED
```

# C. Development order after blocker closure

The sales-blocker phase requested by `/goal` is closed.

Next software target:

`POST ADAPTER v0 DOGFOOD`

Use the real BridgePatch launch/hotfix as the first production-shaped source record and verify that:

1. completed vs planned vs deployed claims remain distinct;
2. Stripe/GitHub evidence bindings survive transformation;
3. X / note / GitHub / Instagram outputs differ meaningfully by channel;
4. unsupported claims fail closed;
5. no external publication occurs without a separate human action.

Real World Roguelike remains:

```text
CLASS: LARGE_VENTURE
LARGE_VENTURE_PRIORITY: 1
STATE: FROZEN
SELECTION: NOT_SELECTED
CURRENT_CYCLE_IMPLEMENTATION: FORBIDDEN
```
