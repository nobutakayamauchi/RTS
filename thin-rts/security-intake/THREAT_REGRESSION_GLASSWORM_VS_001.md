# Threat Regression Capsule — GLASSWORM-VS-001

Status: `ACTIVE_REGRESSION / RAW_PAYLOAD_NOT_EMBEDDED / INHERITED_BY_INTAKE_AND_EGRESS`

Purpose: preserve the transferable failure condition without committing or executing a live malicious payload.

## Observed transferable condition

A source artifact can contain visually unobvious Unicode Variation Selectors that ordinary review may not notice. If downstream code treats those selectors as encoded data and decodes/executes the result, visual review and naïve text comparison can be bypassed.

This capsule is incident-derived but implementation-neutral.

## Frozen invariant

`VISUALLY_INNOCENT != BYTE_INNOCENT`

Before WITNESS consumes external text/code/config, and again before ULTIMATE LOOP/generated material is promoted outward:

1. bind the relevant boundary identities;
2. hash the exact bytes;
3. inspect dangerous/invisible Unicode classes without executing the content;
4. reject or quarantine material that violates the hygiene policy;
5. preserve the failure class as regression memory;
6. admit/promote only material with an explicit CLEAN verdict.

## Regression cases

The committed regression suite synthesizes dangerous codepoints at test runtime rather than storing them literally in normal source files.

Required cases:

- zero-width control in executable text → `BLOCK`;
- `U+FE00..U+FE0F` Variation Selector in executable/config text → `BLOCK`;
- `U+E0100..U+E01EF` supplementary Variation Selector in prose/code → `BLOCK`;
- `.github/workflows/*.yml` must be inside scanner scope;
- ordinary prose emoji presentation selector may remain `CLEAN` under the bounded prose policy;
- explicit unsupported/unscanned intake → `BLOCK`;
- explicit unsupported/unscanned egress → `BLOCK`;
- exact-byte SHA-256 and boundary identities emitted before admission/promotion;
- independent challenger must prove positive detection against generated dynamic-execution attack fixtures before a zero-finding repository scan counts as evidence.

## Non-claims

Passing this regression does not prove:

- absence of all visible malicious code;
- absence of credential theft;
- dependency safety;
- runner/interpreter integrity;
- branch/ruleset correctness;
- secret safety;
- general steganography resistance;
- malware-free status;
- immunity to future unknown attack classes.

Those are separate responsibilities and should preferentially be externalized/composed.

## Inheritance rule

Any future intake implementation, egress implementation, external scanner composition or replacement occupant in the Movable Frame inherits this capsule.

A challenger that cannot pass `GLASSWORM-VS-001` cannot replace the current quarantine occupant even if it is cheaper or simpler.

When a future threat exposes a materially new miss, create a new regression capsule rather than silently broadening this one until its evidence meaning becomes ambiguous.
