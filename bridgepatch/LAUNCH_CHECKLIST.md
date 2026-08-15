# BridgePatch Launch Checklist

Status: `PUBLIC_SALE_ACTIVE / PAYMENT_LINK_V2 / PAGES_BUILD_PASSED`

## Current production state

- [x] Founder explicitly stated `PUBLIC_SALE_APPROVED` on 2026-08-15 JST.
- [x] BridgePatch sales surface merged to `main`.
- [x] Public URL fixed to `https://nobutakayamauchi.github.io/RTS/bridgepatch/`.
- [x] Public contact email fixed to `yamauchi.rts.office@gmail.com`.
- [x] Free consultation CTA uses the public contact email.
- [x] Terms / privacy / commercial disclosure are present in `bridgepatch/`.
- [x] Non-public seller address and reachable phone are available outside the public repository for disclosure/prepayment notices.

## Stripe production link v2

The initially reused legacy Price/Payment Link was rejected during live smoke because its line-item description remained `新規案件 初動フローチャート策定` even after the Product itself had been renamed.

That link is no longer production authority.

Current canonical payment objects:

```text
Product: prod_UAWEhRHXtUTaWb
Product name: BridgePatch 暫定ツール実装設計書
Price: price_1U4ewGPYxtfxmKGliOKXtIP1
Payment Link: plink_1U4ewTPYxtfxmKGlnNEYk9Bs
URL: https://buy.stripe.com/5kQ3cxb5SaTz0LI8jV3Nm0f
Amount: JPY 10,000
Quantity: 1
Adjustable quantity: false
Tax behavior: inclusive
Live mode: true
```

- [x] New dedicated Price created after Product rename.
- [x] New dedicated Payment Link created from the new Price.
- [x] Stripe line-item smoke shows `BridgePatch 暫定ツール実装設計書`.
- [x] Stripe line-item total is JPY 10,000.
- [x] Individual name is required.
- [x] Business name is optional.
- [x] Pre-submit text states product boundary, delivery timing, and cancellation/refund boundary.
- [x] Post-payment message points to `yamauchi.rts.office@gmail.com`.
- [x] `bridgepatch/config.js` on `main` points to the v2 URL.
- [x] GitHub Pages build succeeded for the hotfix commit `fb66986ac60347134ace9f0597871f22ca27e748` with no Pages build error.

## Retired legacy link

```text
Payment Link: plink_1TCBEnPYxtfxmKGlmuK4Cwqe
URL: https://buy.stripe.com/3cI7sN7TG4vb9ie8jV3Nm02
State: INACTIVE
Reason: retained stale line-item description from the pre-BridgePatch product
```

Do not reactivate or reintroduce this URL into production configuration.

## Remaining operational checks

These are operations, not launch blockers:

- [ ] When the first real purchase arrives, send the required intake/follow-up email promptly.
- [ ] If address/phone disclosure is requested, provide the non-public verified values before the customer must decide whether to purchase.
- [ ] If a prepayment notice is legally required for a specific transaction, send the prepared notice with the required seller/contact/provision information.
- [ ] Reopen `/goal` if Stripe restrictions, law/policy changes, broken delivery, unsupported claims, or a material product/price/refund change occurs.

## Current verdict

`BRIDGEPATCH_PUBLIC_SALE_ACTIVE`

The payment-link mismatch found during launch smoke is fixed. The v2 Price/Payment Link is the only canonical public checkout path.
