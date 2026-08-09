# Contributing to RTS

RTS is an evidence-first, Git-native protocol for structurally auditable AI execution.

The core rule is simple:

**If it cannot be verified from repository artifacts, it is not accepted as RTS.**

---

## What to contribute

### 1) Structural Failure Reports (best contribution)
If you find an irreconstructable decision state, report it.

- Use: **Issues → New issue → Structural Failure Report**
- Provide: ledger path, snapshot reference, and reproduction steps.

### 2) Documentation improvements
Clarity, ordering, minimal examples, and verification steps.

### 3) Tooling fixes (scripts / workflows)
Determinism and auditability come first.
No hidden state. No external telemetry.

### 4) Extensions, integrations, and interoperability
Forks, adapters, integrations, external tooling, commercial extensions, and research are welcome when they respect the repository license and provenance requirements.

---

## Hard constraints (non-negotiable)

- **No secrets / tokens / personal data**
- **No inference beyond evidence**
- **No fabricated logs**
- **No destructive history rewrite**
- **No origin/provenance falsification**
- **No malicious or intentionally abusive use**
- **Keep outputs deterministic**
  - Same inputs → same outputs

---

## How to propose changes

1. Create a branch (PR only; `main` is protected)
2. Keep PR scope small
3. Include evidence:
   - file paths
   - before/after diffs
   - reproduction commands (if applicable)
4. Preserve authorship and provenance where prior RTS work is incorporated.

---

## Review policy

High-impact areas require review:

- `sessions/`
- `incidents/`
- `analysis/`
- `.github/workflows/`
- `scripts/`

---

## Communication

- Questions: Discussions
- Bugs / failures: Issues (use templates)
- Security concerns: follow `SECURITY.md` (do **not** open public issues for sensitive reports)

---

## License and contribution terms

By contributing, you agree that accepted contributions may be distributed under the repository's current `LICENSE`, the **RTS Responsible Open Use License v1.0**, unless another arrangement is explicitly accepted in writing by the maintainer.

The project welcomes commercial use, joint development, forks, sponsorship, and funding. Attribution/origin falsification and malicious or intentionally abusive use remain outside the license grant.
