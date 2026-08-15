# Sales Blocker Matrix — 2026-08-15

Status: `AXIS_LIVE / BRIDGEPATCH_PRELAUNCH_HUMAN_GATE`

This matrix supersedes the earlier handoff-based assumptions with current repository, Stripe, GitHub Pages, and official-rule evidence.

Allowed blocker classes:

- `DONE`
- `NOT_BLOCKING`
- `HUMAN_INPUT_REQUIRED`
- `EXTERNAL_ACCOUNT_ACTION_REQUIRED`
- `LEGAL_REVIEW_REQUIRED`
- `TECHNICAL_FIX_REQUIRED`
- `VERIFICATION_REQUIRED`

# A. BridgePatch

| ID | Blocker / requirement | Status | Current evidence | Next action |
|---|---|---|---|---|
| BP-01 | Product boundary and offer ladder | `DONE` | Free fit check, JPY 10,000 portable implementation spec, JPY 50,000 simple tool remain the frozen offer | No redesign |
| BP-02 | Seller/operator identity | `DONE` | `山内 延天（屋号：RS AI）` / operator `山内 延天` | Preserve |
| BP-03 | Public contact email | `DONE` | Fixed by Founder to `yamauchi.rts.office@gmail.com` and staged in all BridgePatch surfaces | Preserve |
| BP-04 | Free consultation route | `DONE` | Staged as a mailto route to the public contact email; no new form is required for v0 | Live smoke after deployment |
| BP-05 | JPY 10,000 Stripe Payment Link | `DONE` | Existing live link `plink_1TCBEnPYxtfxmKGlmuK4Cwqe` reused; URL `https://buy.stripe.com/3cI7sN7TG4vb9ie8jV3Nm02`; product renamed to `BridgePatch 暫定ツール実装設計書`; JPY 10,000; quantity 1; individual name required; business name optional | Live smoke after deployment |
| BP-06 | Paid-intake redirect | `NOT_BLOCKING` | Checkout completion message sends the customer to email follow-up; no intake app is needed | Preserve thin flow |
| BP-07 | Address/phone disclosure method | `DONE` | Current official rule review supports omission from the public ad when disclosure-on-request is stated and information can be supplied without delay before purchase decision; wording staged | Re-review only if law/operation changes |
| BP-08 | Actual non-public seller address/phone availability | `DONE` | Current Stripe account contains a verified non-public seller address and reachable phone number; values are deliberately not committed to the public repository | Retrieve privately when a disclosure/prepayment notice requires them |
| BP-09 | Hosting target / public URL | `DONE` | Existing RTS GitHub Pages deploys from `main` repository root; planned public path is `https://nobutakayamauchi.github.io/RTS/bridgepatch/` | Deploy only after human gate |
| BP-10 | Production config / public documents | `DONE` | `bridgepatch/` now contains config, LP, terms, privacy, commercial disclosure, prepayment notice procedure, and launch checklist with live identifiers and no private seller address/phone | Preserve |
| BP-11 | Stripe purchase-boundary text | `DONE` | Checkout pre-submit text states no tool build, provision timing, and refund/cancellation boundary; post-payment message points to the public contact email | Preserve |
| BP-12 | Cross-page / Pages live smoke | `VERIFICATION_REQUIRED` | Cannot prove the final GitHub Pages route before `bridgepatch/` reaches `main` | Merge/deploy, then run live smoke |
| BP-13 | Stripe Terms-of-Service consent checkbox | `NOT_BLOCKING` | The public terms page is not live before deployment; the checkout already displays the critical service/delivery/refund boundary. Do not break checkout merely to force a pre-deployment checkbox | Reconsider after the live terms URL exists |
| BP-14 | Final public-sale human approval | `HUMAN_INPUT_REQUIRED` | Merging PR #334 will put the staged BridgePatch page on the public GitHub Pages site. The current branch explicitly preserves a human public-sale gate | Obtain one explicit current approval before merge/public deployment |

## BridgePatch /goal conclusion

All non-human prelaunch blockers that can currently be resolved without public deployment are resolved.

Current irreducible sequence:

```text
explicit current human public-sale/deployment approval
-> merge PR #334
-> GitHub Pages build
-> live BridgePatch smoke
-> if smoke passes, public sale active
```

# B. RTS AXIS

The prior handoff used for the first matrix was stale. The current `nobutakayamauchi/RTS-minicompany` main record establishes a later state.

| ID | Requirement | Status | Current evidence | Next action |
|---|---|---|---|---|
| AX-01 | Product / JPY 49,500 / scope | `DONE` | Approved active service profile | Preserve |
| AX-02 | Public seller identity and legal/customer surfaces | `DONE` | Gates A-H and final cross-surface comparison passed before Founder approval | Preserve |
| AX-03 | Explicit `PUBLIC_SALE_APPROVED` | `DONE` | Founder approval recorded 2026-07-23 12:33 JST; Gate I passed | Preserve until a reapproval trigger occurs |
| AX-04 | Repository release | `DONE` | PR #91 merged; release completed | No action |
| AX-05 | note sales page | `DONE` | Published note article identifier `n86c36f6a406c`; controlled public launch active | Keep live unless a pause trigger occurs |
| AX-06 | Inquiry route | `DONE` | Inbound inquiry route open and ready for fit checks | Handle inbound as it arrives |
| AX-07 | Gmail / written-consent / customer-specific Stripe invoice flow | `DONE` | Customer flow and safe pre-send invoice preview approved | Use only for a specific customer after written consent |
| AX-08 | Live invoice / paid work | `NOT_BLOCKING` | No live invoice is authorized without a specific consenting customer; this is an operational customer gate, not a product-launch blocker | Wait for qualifying customer / explicit customer-specific authority |
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
OUTBOUND_CUSTOMER_OUTREACH: NOT GENERALLY AUTHORIZED BY THE AXIS RELEASE RECORD
LIVE_CUSTOMER_INVOICE: CUSTOMER-SPECIFIC CONSENT GATE REQUIRED
```

No new AXIS product-development work is authorized merely because no customer is currently active.

# C. Development order after refresh

- RTS AXIS: already live; do not rebuild it.
- BridgePatch: prepared to the public-deployment human gate.
- Post Adapter v0: already implemented on PR #334; continue dogfood after the BridgePatch launch gate is resolved.
- Real World Roguelike: remains `LARGE_VENTURE_PRIORITY = 1`, `FROZEN`, `NOT_SELECTED`.
