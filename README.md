# RTS

> **Project status: FROZEN / DEVELOPMENT ENDED — 2026-08-09**  
> Formal abolition-test verdict: **EVIDENCE_INSUFFICIENT / REVISE**  
> Engineering continuation decision: **NO**
>
> RTS is preserved as a research prototype, evidence corpus, and historical implementation record. Further RTS-specific Runtime / Controller / Governance Kernel expansion is not authorized under the final engineering decision.
>
> Final records: [`RTS Development Freeze`](docs/audit/RTS_DEVELOPMENT_FREEZE_2026-08-09.md) · [`Final Abolition Gate`](docs/audit/RTS_FINAL_ABOLITION_GATE_2026-08.md)

## Current service: BridgePatch

RTS itself is frozen, but a current service produced from the surrounding development practice is live:

**[BridgePatch / AI業務レスキュー](https://nobutakayamauchi.github.io/RTS/bridgepatch/)** — 「本格システムを入れるほどではない。でも毎週同じ手作業が痛い」という業務を、一工程だけ小さく切って先に直すサービスです。

- 無料：制作可否の受注適合チェック
- 10,000円（税込）：持ち出し可能な暫定ツール実装設計書
- 50,000円（税込）標準：1アクション簡易ツール
- 問い合わせ: `yamauchi.rts.office@gmail.com`

[販売ページを見る](https://nobutakayamauchi.github.io/RTS/bridgepatch/) / [メールで無料確認](mailto:yamauchi.rts.office@gmail.com?subject=BridgePatch%20%E7%84%A1%E6%96%99%E9%81%A9%E5%90%88%E3%83%81%E3%82%A7%E3%83%83%E3%82%AF)

---

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

### 2) State Transition Tracking

RTS tracks transitions between decision states to identify:

- where structural drift began
- where assumptions shifted
- where discontinuities appeared
- which decision altered the trajectory

This enables precise reconstruction after failure.

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

## Open Development and Use

RTS was developed publicly and its source remains inspectable. Development is now frozen; the text below describes the project's use posture, not an active development roadmap.

Legitimate use is intentionally broad. Personal use, research, modification, forks, integrations, commercial products and services, collaboration, sponsorship, and funding are welcome.

Three boundaries are non-negotiable:

1. **Do not falsify origin.** If RTS code, documentation, architecture, or substantial project material is used as a basis, do not knowingly present the resulting work as wholly independent of RTS.
2. **Do not use RTS maliciously.** Intentional harmful or abusive use is outside the license grant.
3. **Do not deploy RTS in bad faith to materially enable such abuse.**

Independent development is not restricted merely because another project reaches a similar idea.

See:

- License → [`LICENSE`](LICENSE)
- Attribution / Acceptable Use → [`docs/legal/USE_POLICY.md`](docs/legal/USE_POLICY.md)
- Public origin chronology → [`docs/genesis/ORIGIN_LEDGER.md`](docs/genesis/ORIGIN_LEDGER.md)

Because the current RTS license includes use restrictions, RTS does **not** claim OSI-approved open-source status. The accurate terms are **source-available** and **open development**.

---

## Documentation

- Final Development Freeze → `docs/audit/RTS_DEVELOPMENT_FREEZE_2026-08-09.md`
- Final Abolition Gate → `docs/audit/RTS_FINAL_ABOLITION_GATE_2026-08.md`
- Manifest → `docs/manifest.md`
- Technical Overview → `docs/technical_overview.md`
- Genesis / History → `docs/genesis/`
- Rulebook → `docs/rulebook/`

---

## License

RTS Responsible Open Use License v1.0.

Commercial use is permitted subject to attribution/origin and prohibited-use conditions.

Copyright (c) 2026 Nobutaka Yamauchi.
