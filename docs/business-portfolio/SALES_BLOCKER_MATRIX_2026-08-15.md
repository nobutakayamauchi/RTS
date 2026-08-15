# Sales Blocker Matrix — 2026-08-15

Status: `BLOCKER_REVIEW_COMPLETE / EXTERNAL_AND_HUMAN_GATES_REMAIN`

Allowed blocker classes:

- `DONE`
- `NOT_BLOCKING`
- `HUMAN_INPUT_REQUIRED`
- `EXTERNAL_ACCOUNT_ACTION_REQUIRED`
- `LEGAL_REVIEW_REQUIRED`
- `TECHNICAL_FIX_REQUIRED`
- `VERIFICATION_REQUIRED`

The purpose of this matrix is to prevent non-software blockers from becoming unnecessary software projects.

# A. BridgePatch

| ID | Blocker / requirement | Status | Evidence state | Exactly one next action |
|---|---|---|---|---|
| BP-01 | Product boundary and offer ladder | `DONE` | Free fit check, JPY 10,000 portable implementation spec, JPY 50,000 simple tool are already defined | No redesign |
| BP-02 | Seller/operator identity | `DONE` | `山内 延天（屋号：RS AI）` / operator `山内 延天` retained in current sales material | Preserve consistently across pages |
| BP-03 | Public contact email | `DONE` | `yamauchi.rts.office@gmail.com` is present in current BridgePatch payment material | Copy the same value into final config/pages |
| BP-04 | Free consultation URL | `HUMAN_INPUT_REQUIRED` | Current kit still requires a real URL; no authoritative final URL was found in retained material | Choose/provide the real consultation URL |
| BP-05 | JPY 10,000 Stripe Payment Link | `EXTERNAL_ACCOUNT_ACTION_REQUIRED` | Input sheet specifies `https://buy.stripe.com/...`, but retained material still shows a placeholder rather than an authoritative live link | Create/confirm the real BP-SPEC-10000 Payment Link in Stripe and record its URL |
| BP-06 | Paid-intake redirect | `NOT_BLOCKING` | Existing material explicitly provides an email-follow-up completion message when no redirect form exists | Use the existing email fallback for v0 launch unless a form already exists |
| BP-07 | Address/phone disclosure method | `LEGAL_REVIEW_REQUIRED` | Current material proposes disclosure on request; legal sufficiency is not established by the development record | Obtain/perform the required current-law review before public launch |
| BP-08 | Jurisdiction text | `LEGAL_REVIEW_REQUIRED` | `site/config.js` requires a final jurisdiction value but no final approved value is established here | Finalize jurisdiction wording during the legal/public-document review |
| BP-09 | Hosting target / public URL | `HUMAN_INPUT_REQUIRED` | Static site can be hosted several ways, but no final BridgePatch public target is established here | Select the production host/public URL |
| BP-10 | Replace all `REPLACE_ME_*` launch values | `TECHNICAL_FIX_REQUIRED` | Kit explicitly requires real launch values | Apply only the approved values to the production config/pages |
| BP-11 | Cross-page and payment-link smoke test | `VERIFICATION_REQUIRED` | Must be run after real values and link exist | Test LP CTA, Stripe amount/product, completion path, and legal-page reachability |
| BP-12 | Final public-sale human approval | `HUMAN_INPUT_REQUIRED` | Publication is consequential and should not be inferred from draft completion | Obtain explicit human approval immediately before public launch |

## BridgePatch /goal conclusion

BridgePatch does **not** need another product-development cycle before launch review.

Current irreducible blockers are:

```text
human real URLs/host choice
+ external Stripe Payment Link action
+ legal/public-document review
+ config replacement
+ smoke test
+ explicit public-sale approval
```

The paid-intake application is removed from the critical path.

# B. RTS AXIS

| ID | Blocker / requirement | Status | Evidence state | Exactly one next action |
|---|---|---|---|---|
| AX-01 | Product boundary / JPY 49,500 price | `DONE` | Product and price are frozen in retained material | No redesign |
| AX-02 | Seller/operator identity | `DONE` | `山内 延天（屋号：RS AI）`, operator `山内 延天` retained | Preserve consistently |
| AX-03 | Stripe basic operational capability | `DONE` | Test customer/product/invoice preview, JPY amount and issuer display were previously verified; no real billing was performed | Preserve the tested invoice method |
| AX-04 | Address/phone public display method | `LEGAL_REVIEW_REQUIRED` | Handoff explicitly leaves this unresolved | Finalize the current-law-compliant display method before publication |
| AX-05 | Public inquiry email | `HUMAN_INPUT_REQUIRED` | Handoff lists final fixation as remaining work | Confirm the single public inquiry address |
| AX-06 | note sales-page body | `TECHNICAL_FIX_REQUIRED` | Handoff lists creation as remaining work | Produce the frozen-scope sales copy from the approved product terms only |
| AX-07 | Actual note sales-page URL | `EXTERNAL_ACCOUNT_ACTION_REQUIRED` | No final published sales URL exists in the retained handoff | Create the note page only after copy/public-display review is complete |
| AX-08 | Gmail inquiry -> fit check -> written consent workflow | `TECHNICAL_FIX_REQUIRED` | Flow is approved conceptually but still requires final operational artifact alignment | Finalize one canonical intake/consent operating procedure |
| AX-09 | Customer-specific Stripe invoice after consent | `VERIFICATION_REQUIRED` | Method was tested, but real customer billing must not occur during preparation | Perform a final non-customer rehearsal against the canonical procedure |
| AX-10 | Customer-facing external-service/storage disclosures | `TECHNICAL_FIX_REQUIRED` | Approved OpenAI/Gmail/Drive/Oracle/Stripe arrangement still needs consistent customer-document reflection | Update and cross-check the customer documents |
| AX-11 | Sales page / terms / privacy / Stripe wording cross-check | `VERIFICATION_REQUIRED` | Handoff explicitly requires horizontal consistency check | Run one cross-document review after AX-04 through AX-10 are resolved |
| AX-12 | Remaining public-sale gates F-H | `VERIFICATION_REQUIRED` | Earlier gates passed; remaining publication gates were not complete | Re-run and record Gate F-H results |
| AX-13 | `PUBLIC_SALE_APPROVED` | `HUMAN_INPUT_REQUIRED` | Existing handoff explicitly says `PUBLIC_SALE_APPROVED: NO` | Ask the Founder for explicit approval only after AX-12 passes |

## RTS AXIS /goal conclusion

RTS AXIS does **not** need a new analysis engine or new product features before public-sale review.

Current irreducible blockers are:

```text
legal/public display decision
+ final public inquiry identity
+ sales-page copy
+ operational intake/consent artifact
+ customer-document alignment
+ rehearsal/cross-check
+ Gate F-H
+ explicit PUBLIC_SALE_APPROVED
```

The existing rule survives unchanged:

```text
note page
-> Gmail inquiry
-> free fit check
-> written terms/scope
-> explicit consent
-> customer-specific Stripe invoice
-> payment confirmation
-> paid work
```

No shared instant-buy link is introduced.

# C. Next development authorization

The blocker review required by `/goal` is now complete.

Therefore the next software build target becomes:

`POST ADAPTER v0`

This does **not** authorize:

- BridgePatch publication;
- RTS AXIS publication;
- real customer invoices;
- payment collection;
- direct social posting;
- Real World Roguelike implementation.

Those actions remain behind their respective human/external gates.
