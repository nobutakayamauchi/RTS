# Threat Regression Capsule — GLASSWORM-VS-001

Status: `ACTIVE_REGRESSION / RAW_PAYLOAD_NOT_EMBEDDED`

Purpose: preserve the transferable failure condition without committing or executing a live malicious payload.

## Observed transferable condition

A source artifact can contain visually unobvious Unicode Variation Selectors that ordinary review may not notice. If downstream code treats those selectors as encoded data and decodes/executes the result, visual review and naïve text comparison can be bypassed.

This capsule is intentionally incident-derived but implementation-neutral.

## Frozen invariant

`VISUALLY_INNOCENT != BYTE_INNOCENT`

Before WITNESS or any learning/promotion path consumes external text/code/config:

1. bind the external source identity;
2. hash the exact bytes;
3. inspect dangerous/invisible Unicode classes without executing the content;
4. reject or quarantine material that violates the hygiene policy;
5. preserve the failure class as regression memory;
6. admit only normalized, evidence-bound learning into ULTIMATE LOOP.

## Regression cases

The committed regression suite synthesizes the dangerous codepoints at test runtime rather than storing them literally in normal source files.

Required cases:

- zero-width control in executable text → `BLOCK`;
- `U+FE00..U+FE0F` Variation Selector in executable/config text → `BLOCK`;
- `U+E0100..U+E01EF` supplementary Variation Selector in prose/code → `BLOCK`;
- `.github/workflows/*.yml` must be inside scanner scope;
- ordinary prose emoji presentation selector may remain `CLEAN` under the bounded prose policy;
- explicit unsupported/unscanned intake → `BLOCK`;
- exact-byte SHA-256 and source identity emitted before WITNESS admission.

## Non-claims

Passing this regression does not prove:

- absence of visible malicious code;
- absence of credential theft;
- dependency safety;
- runner/interpreter integrity;
- branch/ruleset correctness;
- secret safety;
- general steganography resistance;
- malware-free status.

Those are separate responsibilities and should preferentially be externalized/composed.

## Inheritance rule

Any future intake implementation, external scanner composition or replacement occupant in the Movable Frame inherits this capsule.

A challenger that cannot pass `GLASSWORM-VS-001` cannot replace the current intake occupant even if it is cheaper or simpler.
