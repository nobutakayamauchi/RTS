# RTS Rulebook (EN)
## Structural Governance Specification v1.0

---

## 0. Purpose

This document defines the structural contract of RTS.

RTS is not a logging framework.  
RTS is a reconstructability protocol.

RTS guarantees structural reproducibility of decision state — not outcome correctness.

This is an operational specification, not an academic paper.

---

# 1. Structural Principles

RTS operates under the following axioms.

## 1.1 Reconstructability First

RTS prioritizes reconstruction of decision state over reproduction of output.

If a decision cannot be reconstructed,
it cannot be defended.

If it cannot be defended,
it cannot scale.

---

## 1.2 Append-Only Ledger

Session records are immutable and append-only.

Past execution state is never modified.

Integrity precedes convenience.

---

## 1.3 Deterministic Aggregation

Monthly indices must be deterministically generated from ledger data.

No hidden transformations.
No non-reproducible aggregation.

---

## 1.4 Breakpoint-Based Sealing

RTS does not react to noise.
RTS reacts to structural mutation.

When mutation density crosses a defined boundary:

1. State is sealed
2. Snapshot is generated
3. Evidence Snapshot (ESC) is created
4. Reference becomes immutable

This is not monitoring.
This is structural sealing.

---

# 2. Design Decision Criteria

When structural ambiguity arises, decisions are evaluated against four principles.

---

## 2.1 Simplicity

- Is the structure traceable?
- Is the placement obvious?
- Can future changes be located without friction?
- Does this reduce structural entropy?

If in doubt, choose the simpler structure.

Complexity compounds silently.

---

## 2.2 Directness

- Is this aligned with the primary structural path?
- Is this a workaround?
- Is this avoiding the real design issue?

RTS does not detour.
Structure must remain linear and intelligible.

---

## 2.3 Structural Cleanliness

- Is this relying on temporary tricks?
- Will this be understandable months later?
- Is this a patch or a decision?

If uncertain, remove rather than layer.

Local optimization must not compromise structural clarity.

---

## 2.4 Usability (Self-Operability)

The primary user of RTS is its operator.

- Can the operator locate state immediately?
- Can structure be understood without interpretation?
- Is friction introduced?

Usability failure is structural failure.

---

## 2.5 AI-Cooperative Placement Principle

RTS is built in AI collaboration.

When placement decisions are unclear:

- Do not rely solely on human intuition.
- Evaluate machine readability.
- Prioritize structural predictability.
- Consult AI to determine the most structurally coherent location.

Placement must optimize:

- Machine parsability
- State traceability
- Long-term inference stability

Structure is decided by rational coherence, not aesthetic preference.

---

# 3. Artifact Contract

RTS produces four canonical artifacts:

- Session Ledger (JSONL)
- Monthly Index
- Snapshot
- Evidence Snapshot (ESC)

Verification must derive exclusively from artifacts.

If a claim cannot be verified from artifacts, it is not RTS.

---

# 4. Mutation Handling Model

RTS distinguishes between noise and structural mutation.

Only structural mutation triggers escalation.

Breakpoint detection results in:

1. State freezing
2. ESC generation
3. Snapshot immutability
4. Reference stabilization

RTS does not predict correctness.
RTS preserves structural traceability.

---

# 5. Non-Goals

RTS does not guarantee:

- Ethical correctness of decisions
- Legal compliance
- Semantic validity
- Outcome success
- Moral evaluation
- Autonomous repair

RTS guarantees only:

Structural reconstructability.

Nothing more.
Nothing less.

---

# 6. Why These Rules Exist

RTS is developed under constraints:

- Single-device environment
- GitHub-native editing
- No local IDE dependency
- Browser-based operation
- AI-assisted authorship

These constraints are intentional design boundaries.

Certain operational rules exist because:

- Multi-line patching degrades stability in constrained contexts
- Context accumulation reduces AI output reliability
- Structural clarity outweighs local efficiency

RTS favors coherence over convenience.

---

# 7. Constraint as Discipline

Constraints are not weaknesses.
They are structural boundaries.

RTS must remain reconstructable even under minimal tooling conditions.

- No hidden infrastructure
- No opaque backend
- No privileged environment

If it cannot survive constraints,
it is not structurally sound.

---

# 8. Finite Sessions

AI collaboration sessions are finite.

Context inflates.
Latency increases.
Output quality degrades.

Resetting context is not failure.
It is architectural hygiene.

---

# 9. Final Principle

RTS does not pursue perfection.

RTS pursues inspectability.

If it cannot be reconstructed,
it cannot be defended.

If it cannot be defended,
it cannot endure.

End of specification.
