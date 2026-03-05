# RTS Repository Structure Map

This document defines the structural intent of the repository.

RTS preserves execution structure.  
The repository itself follows the same principle.

---

## 1️⃣ Root Layer (Operational + Public Interface)

The root directory serves two purposes:

- System operation
- Public documentation entry points

Core operational directories:

- `.github/`
- `sessions/`
- `analysis/`
- `incidents/`
- `docs/`

Core system files:

- `README.md`
- `LICENSE`

Public interface files (allowed at root):

- `START.md`
- `_LATEST.md`
- `SECURITY.md`
- `SENTINEL_CHARTER.md`
- `USE_CASES.md`
- `STRUCTURE_MAP.md`

Root may also contain:

- Static site files (`index.md`, `index.html`, `search.html`)
- Generated artifacts required for Pages

Nothing unrelated to system operation or public interface should remain at root.

---

## 2️⃣ Documentation Layer (`/docs/`)

Human-readable extended documentation lives under `/docs/`.

- `manifest.md` → Core declaration
- `technical_overview.md` → System explanation
- `genesis/` → Historical origin
- `rulebook/` → Operational doctrine
- `research/` → Experimental evolution
- `archive/` → Deprecated but preserved history

---

## 3️⃣ Operational Rule

When in doubt:

1. If it runs the system → keep at root.
2. If it is public entry documentation → keep at root.
3. If it explains or expands → move to `/docs/`.
4. If historical or experimental → move to `/docs/research` or `/docs/archive`.
5. Never delete history. Move instead.

---

RTS applies its structural doctrine to itself.
