# RTS

Decision Reconstructability Protocol for AI-Accelerated Systems.

RTS guarantees reconstructability — not correctness.

It records decision states so structural drift and discontinuities can be located, audited, and reduced over time.

---

## The Problem

AI accelerates execution.

But decision authority is rarely recorded.

When systems fail, the same question appears:

**Who approved this — and under what assumptions?**

Most AI workflows cannot reconstruct the decision state after the fact.
RTS exists to preserve that state.

---

## What RTS Is

RTS is a **Git-native structural ledger** for decisions and execution.

It preserves:

- decision authority (who approved what)
- execution structure (what happened, in what order)
- state transitions (what changed and when)

RTS logs **structure**, not semantics.
It is designed for auditability, continuity, and post-failure reconstruction.

---

## How RTS Works

RTS introduces a structural decision layer built on Git.

### 1) Decision State Snapshot

Each block records:

- Context
- Decision
- Constraints
- Assumptions
- Action
- Outcome

This forms a reconstructable decision snapshot.

### 2) State Transition Tracking

RTS tracks state transitions so you can identify:

- where the structure changed
- where assumptions shifted
- where discontinuities appeared

### 3) Append-Only Ledger

RTS is deterministic and Git-native.

- commits act as immutable timestamps
- history becomes operational evidence
- reconstruction remains possible even when memory is lost

### 4) Decision Boundary Layer (Optional)

RTS can record a boundary event that captures:

- approver / authority holder
- scope of responsibility
- justification at the time of approval
- commit hash (state at approval time)

This is **not blame**.
It is an authority trace.

---

## Minimal Flow

1. Create a decision block
2. Commit the state
3. Record a boundary (optional)
4. Reconstruct anytime

---

## What RTS Is Not

RTS is not:

- workflow automation
- monitoring software
- compliance software
- memory embedding / vector retrieval

RTS is a **structural ledger**.

---

## Documentation

- Manifesto → `docs/manifesto.md`
- Technical Overview → `docs/technical_overview.md`
- Genesis / History → `docs/genesis/`
- Rulebook → `docs/rulebook/`

---

## License

MIT
