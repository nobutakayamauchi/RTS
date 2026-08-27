# Model Transition Intelligence + Architecture Contract Diff v1

H is the documentation-side transition layer that sits before F/G.

```text
old official docs + new official docs
        ↓
immutable Version Evidence Bundles
        ↓
normalized anchored contract claims
        ↓
H: external contract diff + S0/S1/S2/S3
        ↓
profile disposition + bounded probe requirements
        ↓
F: measure actual behavior
        ↓
G: execute approved bounded campaign
```

## What H means by "architecture"

H does **not** infer hidden neural architecture. `S3` means an **observable execution-contract shift**: for example, the documented owner/topology of the agent loop, delegation, state model, sandbox model, memory model, or tool execution model changes.

`DOCS CLAIM != OBSERVED BEHAVIOR` is a hard invariant. Every documentation delta is emitted with `behavior_status=UNVERIFIED`; F/G must measure it before an operating profile becomes evidence-backed.

## Evidence Bundle

Each source carries:

- stable `document_id` across generations;
- exact `url` and `ref`;
- full supplied document `content` and exact SHA-256 digest;
- trust class (`OFFICIAL` or `UNOFFICIAL`);
- normalized claims, each anchored to exact text contained in that document.

H performs no crawling or LLM semantic extraction in v1. A future provider-specific source adapter can fetch README/release notes/API docs/model cards/migration guides and an extraction boundary can propose normalized claims, but the comparator itself remains deterministic and network-free. H verifies that every supplied claim is anchored in the immutable source text and never treats the extracted claim set as complete merely because at least one claim changed.

For an official document present in both generations, H removes only the anchors belonging to the actual normalized claim deltas from the old and new document text. If the residual document text still differs, the transition becomes `REVIEW_REQUIRED`. This prevents one mapped marketing change from hiding a second, unextracted execution-contract change in the same README or migration guide.

Only `OFFICIAL` claims can raise transition severity. Unofficial material can be carried for context but cannot establish a contract change.

## Severity

- `S0`: no material external contract change; marketing/wording only.
- `S1`: tuning, limits, pricing/performance, or identity-level change.
- `S2`: documented behavior/interface/tool semantics changed.
- `S3`: observable execution-contract topology changed.

Conflicting official claims, digest/provenance failures, or changed official text that is not fully accounted for by normalized claim deltas fail to `REVIEW_REQUIRED` rather than pretending nothing changed.

## Authority

H never grants execution, profile-application, or promotion authority. Even at S3 it preserves historical profiles as evidence and only blocks their direct reuse until F/G revalidation.

## Completion boundary

`RTS-FRZ-000018` is complete only as this deterministic comparison/gating layer. Provider-specific document discovery, crawling, claim extraction, actual model execution, and runtime policy mutation are separate future boundaries. Completion does not claim those capabilities already exist.
