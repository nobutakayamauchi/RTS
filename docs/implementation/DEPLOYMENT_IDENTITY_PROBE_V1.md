# RTS Runtime Debugging Identity and Evidence Gates v1

## Purpose

Prevent RTS debugging from classifying repository code as runtime reality, promoting a mapped code location into a root-cause claim, or declaring a fix validated without deployment-bound evidence.

## Canonical invariants

> Deployment Identity MUST be established before runtime implementation classification.

> Code existence != runtime evidence.

> Runtime-to-code mapping is not a root-cause claim.

> Root-cause claims require support, reproduction, falsification, and no unresolved counterevidence.

> A fix is not validated until post-patch deployment identity is established and the retest is evidence-bound to it.

All components are read-only decision gates. They grant no deployment, restart, rollback, source mutation, FREEZER mutation, or build authority.

## Pipeline

```text
Observation
→ Deployment Identity Probe
→ Runtime Debug Gate
→ Runtime Evidence Correlation
→ Runtime Code Mapping Gate
→ Root Cause Claim Gate
→ Patch proposal / external implementation step
→ Deployment Re-Identity
→ Retest / Regression Gate
→ FIX_VALIDATED or return to analysis
```

## 1. Deployment Identity Probe

Collects evidence-bound identity fields:

- host and pid;
- service/unit;
- working directory;
- executable;
- entrypoint/module;
- active route;
- deployed commit/revision;
- optional artifact SHA-256.

States are `ESTABLISHED`, `PARTIAL`, `UNKNOWN`, and `CONFLICT`.

`ESTABLISHED` requires working directory, executable, entrypoint, deployed revision, and at least one runtime anchor (`service_unit` or `active_route`). All other states fail closed for runtime classification.

## 2. Runtime Debug Gate

Consumes an observation plus deployment identity.

- missing identity → `BLOCKED_IDENTITY_MISSING`;
- non-established identity → `BLOCKED_IDENTITY_NOT_ESTABLISHED`;
- established identity → `READY_FOR_EVIDENCE_CORRELATION`.

Even the ready state keeps runtime implementation `UNCLASSIFIED`. Identity alone never identifies source code.

## 3. Runtime Evidence Correlation

Candidate source records must contain candidate ID, source reference, revision, and runtime evidence references.

- revision mismatch → `REJECTED_REVISION_MISMATCH`;
- revision match without runtime evidence → `BLOCKED_MISSING_RUNTIME_EVIDENCE`;
- revision match plus evidence → candidate becomes eligible for code mapping.

Exactly one eligible candidate is required. Zero candidates or multiple candidates fail closed.

## 4. Runtime Code Mapping Gate

The single correlated candidate must match the proposed source reference and provide:

- one or more mapped symbols; and
- one or more mapping evidence references.

Success produces `READY_FOR_ROOT_CAUSE_ANALYSIS` while keeping `root_cause_claim_allowed=false`.

## 5. Root Cause Claim Gate

Each hypothesis must provide:

- supporting evidence;
- reproduction evidence;
- falsification-attempt evidence; and
- zero unresolved counterevidence.

A hypothesis pointing to another candidate fails closed. Missing reproduction, missing falsification, missing support, or unresolved counterevidence blocks promotion.

Exactly one eligible hypothesis produces `ROOT_CAUSE_CLAIM_SUPPORTED`. Multiple supported hypotheses remain ambiguous. This gate never validates a fix.

## 6. Retest and Deployment Re-Identity Gate

After a patch or deployment change, the post-patch deployment identity MUST be collected and reach `ESTABLISHED` again.

The retest must:

- refer to the selected root-cause claim;
- name the exact post-patch deployed revision;
- match the re-established identity revision;
- contain verification evidence;
- contain regression evidence; and
- report `PASS` or `FAIL`.

Only `PASS` with both verification and regression evidence produces `FIX_VALIDATED`. A failed retest returns to root-cause analysis. A nominal pass with incomplete evidence remains blocked.

## Fail-closed rules

- Repository file existence never creates runtime authority.
- Stale or non-deployed revisions cannot enter code mapping.
- Similar-looking source code without runtime evidence cannot enter code mapping.
- Multiple correlated candidates cannot be silently selected.
- Code mapping cannot manufacture root-cause authority.
- Root-cause authority cannot be manufactured without reproduction and falsification evidence.
- Unresolved counterevidence blocks root-cause promotion.
- Root-cause support cannot manufacture fix validation.
- A retest bound to a revision different from the re-established deployed revision is rejected.
- A passing retest without verification and regression evidence does not validate the fix.

## CLI for deployment identity

```bash
python -m deployment_identity.cli probe \
  --service-unit rts.service \
  --active-route https://example.invalid/health \
  --deployed-revision <commit> \
  --entrypoint app.py \
  --require-established
```

Validation:

```bash
python -m deployment_identity.cli verify deployment_identity.json --require-established
```

Exit codes: `0` gate passed, `1` invalid input/snapshot, `2` valid identity snapshot but not `ESTABLISHED` when establishment is required.

## Implemented modules

- `deployment_identity/`
- `runtime_debug_gate/`
- `runtime_evidence_correlation/`
- `runtime_code_mapping/`
- `root_cause_claim_gate/`
- `retest_reidentity_gate/`

## CI acceptance boundary

The dedicated workflow compiles all six modules, executes all focused success and fail-closed tests, verifies missing-revision failure, verifies established identity, verifies missing-identity blocking, verifies stale-revision rejection, and executes one synthetic end-to-end path through root-cause support and post-patch re-identity to `FIX_VALIDATED`.

The workflow is read-only and does not deploy or patch a runtime.
