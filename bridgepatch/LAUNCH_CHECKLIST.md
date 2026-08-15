# BridgePatch Launch Checklist

Status: `PRELAUNCH / DO NOT PUBLISH OR ANNOUNCE UNTIL HUMAN APPROVAL`

## Already completed in this branch

- [x] Public contact email fixed to `yamauchi.rts.office@gmail.com`
- [x] Free consultation CTA bound to the public contact email
- [x] Existing live Stripe Payment Link identified and reused
- [x] Stripe product renamed to `BridgePatch 暫定ツール実装設計書`
- [x] Stripe amount remains JPY 10,000 / one-time / quantity 1
- [x] Stripe individual name collection enabled and required
- [x] Stripe business name collection enabled and optional
- [x] Stripe pre-submit text states product boundary, provision timing, and refund/cancellation boundary
- [x] Stripe post-payment message points to the public contact email
- [x] GitHub Pages deployment identity confirmed: `main` repository root -> `https://nobutakayamauchi.github.io/RTS/`
- [x] Planned BridgePatch public path fixed to `/RTS/bridgepatch/`
- [x] Terms / privacy / commercial disclosure staged
- [x] Address and telephone disclosure-on-request wording staged
- [x] Prepayment follow-up email procedure staged without committing private seller data

## Must remain true before public sale

- [ ] `bridgepatch/` is merged to `main`
- [ ] GitHub Pages build succeeds on the merged commit
- [ ] `https://nobutakayamauchi.github.io/RTS/bridgepatch/` returns the expected BridgePatch page
- [ ] Free consultation button opens `yamauchi.rts.office@gmail.com`
- [ ] JPY 10,000 button opens exactly `https://buy.stripe.com/3cI7sN7TG4vb9ie8jV3Nm02`
- [ ] Checkout visibly shows JPY 10,000 and quantity 1
- [ ] Checkout visibly shows the service boundary / delivery timing / cancellation-refund text
- [ ] `tokusho.html`, `terms.html`, `privacy.html` are reachable from the sales page
- [ ] No `REPLACE_ME`, placeholder email, placeholder URL, test customer, or private seller address/phone appears in public files
- [ ] Private seller address and telephone are available outside the public repository for disclosure requests and any required prepayment notice
- [ ] Human reviews the final live pages and explicitly states `PUBLIC_SALE_APPROVED`

## Do not do before `PUBLIC_SALE_APPROVED`

- Do not announce the product as publicly on sale.
- Do not send the Payment Link to a real prospect as the finalized public offer.
- Do not treat a Pages build as legal or commercial approval.
- Do not place private seller address or phone number in the public repository merely to satisfy an internal placeholder.
