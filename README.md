# RTS

Structural Decision & Execution Ledger for AI Systems.

RTS is a Git-native protocol that preserves:

- decision authority  
- execution structure  
- state transitions  

RTS guarantees reconstructability — not correctness.

---

## Decision Boundary

RTS introduces a structural decision boundary layer.

A decision boundary records:

- who approved a structural change  
- the scope of responsibility  
- the justification at the time of approval  
- the commit state (hash)  

This is not a blame system.

It is an authority trace.

RTS separates:

- human decision ownership  
from  
- system behavioral outcome  

This prevents post-failure confusion about:
- who decided  
- what was approved  
- under which assumptions  

---

## What RTS Preserves

Each block records:

- Context  
- Decision  
- Constraint  
- Assumption  
- Action  
- Outcome  

RTS logs structure, not semantics.

---

## What RTS Is Not

RTS is not:

- memory embedding  
- vector retrieval  
- workflow automation  
- monitoring software  
- compliance software  

It is a structural ledger.

---

## Minimal Flow

1. Create block  
2. Log decision  
3. Commit  
4. (Optional) Record decision boundary  
5. Reconstruct state later  

---

## Why RTS

AI accelerates execution.

But authority is rarely recorded.

When systems fail, the same question appears:

**Who approved this?**

RTS anchors that answer.

---

## Documentation

- Manifesto → docs/manifesto.md  
- Technical Overview → docs/technical_overview.md  
- Genesis / History → docs/genesis/  
- Rulebook → docs/rulebook/  

---

## License

MIT
