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

H performs no crawling in v1. A future provider-specific source adapter can fetch README/release notes/API docs/model cards/migration guides and build the bundle, but the comparator itself remains deterministic and network-free.

Only `OFFICIAL` claims can raise transition severity. Unofficial material can be carried for context but cannot establish a contract change.

## Severity

- `S0`: no material external contract change; marketing/wording only.
- `S1`: tuning, limits, pricing/performance, or identity-level change.
- `S2`: documented behavior/interface/tool semantics changed.
- `S3`: observable execution-contract topology changed.

Conflicting official claims, digest/provenance failures, or changed official text that is not mapped to normalized claims fail to `REVIEW_REQUIRED` rather than pretending nothing changed.

## Authority

H never grants execution, profile-application, or promotion authority. Even at S3 it preserves historical profiles as evidence and only blocks their direct reuse until F/G revalidation.
