# RTS Repository Structure Map

This file defines the structural intent of the repository.

RTS preserves execution structure.
The repository itself follows the same principle.

---

## Root Layer (Operational Surface)

Files and directories required for system operation:

- README.md
- LICENSE
- .github/
- scripts/
- sessions/
- analysis/
- incidents/
- docs/

Nothing else should remain at root.

---

## Documentation Layer (Human Readable)

Located under `/docs/`

- manifesto.md → Core declaration
- technical_overview.md → System explanation
- genesis/ → Historical origin and evolution
- rulebook/ → Operational doctrine
- research/ → Experimental evolution documents
- archive/ → Deprecated but preserved history

---

## Principle

When in doubt:

1. If it runs the system → keep at root.
2. If it explains the system → move to docs/.
3. If it is historical or experimental → move to docs/research or docs/archive.
4. Never delete history. Move instead.

---

RTS applies its own structural doctrine to itself.
