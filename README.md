# RTS

Decision Reconstructability Protocol for AI-accelerated systems.

Acceleration without reconstructability leads to structural collapse.

RTS preserves decision states so structural drift and discontinuities can be located and reduced over time.

Repository position: see [docs/overview/POSITION.md](docs/overview/POSITION.md).

---

## The Problem

AI accelerates execution.

But decision authority is rarely recorded.

When systems fail, the same question appears:

**Who approved this — and under what assumptions?**

Most AI workflows optimize execution.  
They do not preserve decision state.

RTS exists to preserve that state.

---

## What RTS Is

RTS is a Git-native structural ledger for decision systems.

It preserves:

- decision authority
- execution structure
- state transitions

RTS logs **structure — not semantics**.

It is designed for auditability, continuity, and post-failure reconstruction.

---

## Core Mechanism

The RTS core consists of three structural guarantees.

### 1) Decision State Snapshot

Each block records:

- Context
- Decision
- Constraints
- Assumptions
- Action
- Outcome

This forms a reconstructable decision state.

---

### 2) State Transition Tracking

RTS tracks transitions between decision states to identify:

- where structural drift began
- where assumptions shifted
- where discontinuities appeared
- which decision altered the trajectory

This enables precise reconstruction after failure.

---

### 3) Append-Only Ledger

RTS is deterministic and Git-native.

- commits act as immutable timestamps
- history becomes operational evidence
- reconstruction remains possible even when memory is lost

The system guarantees reconstructability of structure.

---

## Extensions (Optional Layers)

The following components extend the core.

### Decision Boundary Layer

RTS can record boundary events capturing:

- approver / authority holder
- scope of responsibility
- justification at approval time
- commit hash (state at approval)

This is **not blame**.  
It is an authority trace.

Additional extensions may include:

- drift analysis
- governance history
- failure freeze snapshots (ESC)
- identity modeling

All extensions depend on the core reconstructability model.

---

## Minimal Flow

1. Create decision block  
2. Commit  
3. (Optional) Record boundary  
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

- Manifest → `docs/manifest.md`
- Technical Overview → `docs/technical_overview.md`
- Genesis / History → `docs/genesis/`
- Rulebook → `docs/rulebook/`

---

## License

MIT
