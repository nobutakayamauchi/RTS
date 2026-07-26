# RTS Evidence-Backed Project Outputs

This document summarizes six repository-observed outputs from the RTS governed pilot. Each statement is bounded by committed evidence, separates human direction from AI-tool assistance, and states what has not yet been established.

## 1. A governed loop that turns project intent into a verifiable, resumable workflow

RTS includes a deterministic, repository-local loop that ingests a Seed contract, links eight verification stages, records checkpoints, and stops at explicit human gates. The current implementation is read-only and does not grant unattended execution authority.

**Why it matters:** Complex AI-assisted projects can preserve scope, evidence, review state, and recovery points instead of depending on a single uninterrupted conversation.

**Evidence:** Verified through committed Seed, run, lifecycle, checkpoint, resume, completion, and CI records in RTS. PRs: [#242](https://github.com/nobutakayamauchi/RTS/pull/242), [#243](https://github.com/nobutakayamauchi/RTS/pull/243), [#244](https://github.com/nobutakayamauchi/RTS/pull/244), [#245](https://github.com/nobutakayamauchi/RTS/pull/245), [#246](https://github.com/nobutakayamauchi/RTS/pull/246), [#247](https://github.com/nobutakayamauchi/RTS/pull/247), [#248](https://github.com/nobutakayamauchi/RTS/pull/248), [#254](https://github.com/nobutakayamauchi/RTS/pull/254), [#258](https://github.com/nobutakayamauchi/RTS/pull/258), and [#260](https://github.com/nobutakayamauchi/RTS/pull/260).

**Human role:** Set the usable-loop objective and scope; defined safety, ordering, and completion boundaries; reviewed failures and accepted the bounded result.

**AI-tool role:** Proposed decomposition and implementation details; generated code, fixtures, records, and tests; applied review-driven corrections.

**Limits:** Demonstrated inside RTS as a governed project output. Production autonomy and effectiveness outside this repository are not established.

## 2. One active work item in the governed pilot, with human approval at consequential transitions

During the governed pilot, RTS enforced WIP=1 across selection, implementation, verification, and completion, while explicit human decisions controlled consequential transitions.

**Why it matters:** A single active work item reduces parallel scope drift and makes it clearer which change is being evaluated, approved, completed, or stopped.

**Evidence:** Verified in the lifecycle and approval records for the governed pilot. PRs: [#246](https://github.com/nobutakayamauchi/RTS/pull/246), [#248](https://github.com/nobutakayamauchi/RTS/pull/248), [#253](https://github.com/nobutakayamauchi/RTS/pull/253), [#255](https://github.com/nobutakayamauchi/RTS/pull/255), [#257](https://github.com/nobutakayamauchi/RTS/pull/257), and [#260](https://github.com/nobutakayamauchi/RTS/pull/260).

**Human role:** Set the WIP and approval policy; made priority and continuation decisions; approved lifecycle transitions.

**AI-tool role:** Generated lifecycle records and verification support.

**Limits:** This is a process result observed in the RTS pilot, not evidence that the same policy is optimal for every team or organization.

## 3. Append-only human decisions with fail-closed integrity checks

RTS includes a Human Review Ledger that preserves decisions as an append-only chain and rejects expired or stale decisions, proposer mismatches, unmanifested decision files, and other invalid review states.

**Why it matters:** The system can distinguish a recorded human decision from stale, altered, or unregistered material before any later application step is considered.

**Evidence:** Verified through ledger fixtures, deterministic fingerprints, integrity checks, regression tests, and accepted review corrections. PRs: [#249](https://github.com/nobutakayamauchi/RTS/pull/249), [#250](https://github.com/nobutakayamauchi/RTS/pull/250), [#252](https://github.com/nobutakayamauchi/RTS/pull/252), [#253](https://github.com/nobutakayamauchi/RTS/pull/253), [#254](https://github.com/nobutakayamauchi/RTS/pull/254), and [#255](https://github.com/nobutakayamauchi/RTS/pull/255).

**Human role:** Defined the decision contract and authority boundary; judged review findings and required fail-closed handling; accepted the corrected result.

**AI-tool role:** Implemented the ledger, verification, and regression tests; applied review-driven repairs.

**Limits:** The ledger records and verifies review evidence; it does not itself authorize publication, contracts, external execution, or repository writes.

## 4. Inspect intended changes and rollback points before granting write authority

RTS includes a non-applying Promotion Application Preview that exposes target files, before-and-after hashes, blockers, validation steps, and rollback anchors before any write authority is granted.

**Why it matters:** An operator can examine what would change, how it would be checked, and where recovery would begin without applying the change.

**Evidence:** Verified through the committed preview schema, deterministic fixtures, parser-based inspection, safety checks, and CI tests. PRs: [#256](https://github.com/nobutakayamauchi/RTS/pull/256), [#257](https://github.com/nobutakayamauchi/RTS/pull/257), and [#258](https://github.com/nobutakayamauchi/RTS/pull/258).

**Human role:** Defined scope, safety constraints, and acceptance boundaries; reviewed the non-applying result.

**AI-tool role:** Implemented the schema, preview logic, fixtures, and tests.

**Limits:** The preview is intentionally non-applying. It does not write to a target repository or approve the proposed change.

## 5. Governance depth derived from declared change and authority context

RTS includes an Adaptive Governance Compiler that deterministically selects G0-G4 governance profiles from the requested action, affected paths, reversibility, and authority context. Independent review findings were incorporated as fail-closed fixes and regression tests.

**Why it matters:** Low-risk work can avoid unnecessary ceremony while sensitive or irreversible work retains stronger review, rollback, and testing requirements.

**Evidence:** Verified through deterministic compilation, context-bound verification, fixed profiles, independent review findings, accepted repairs, and full regression tests. PR: [#259](https://github.com/nobutakayamauchi/RTS/pull/259).

**Human role:** Defined the governance model and risk thresholds; judged review findings material; required and accepted fail-closed corrections.

**AI-tool role:** Implemented the compiler and tests; raised independent review findings; implemented repairs and reran validation.

**Limits:** The compiler has been tested inside RTS. It does not prove universal risk-classification quality or replace human judgment for consequential decisions.

## 6. From a long project conversation to a machine-verifiable Seed and scope decision

A long project conversation was converted into a verified Seed Pack, ingested by the governed loop, and reduced to a bounded P0 scope decision with explicit future branches and stopping conditions.

**Why it matters:** Unstructured intent can become a resumable project contract that preserves goals, constraints, exclusions, privacy boundaries, and the next human decision.

**Evidence:** The Seed Pack, manifest, scope profiles, P0 run, checkpoint, and related CI records are verified in RTS. PRs: [#247](https://github.com/nobutakayamauchi/RTS/pull/247), [#254](https://github.com/nobutakayamauchi/RTS/pull/254), [#258](https://github.com/nobutakayamauchi/RTS/pull/258), [#259](https://github.com/nobutakayamauchi/RTS/pull/259), [#260](https://github.com/nobutakayamauchi/RTS/pull/260), and [#261](https://github.com/nobutakayamauchi/RTS/pull/261).

**Human role:** Synthesized the product direction and selected scope; set privacy and stopping boundaries; required reconstruction and recovery evidence.

**AI-tool role:** Structured documents and validation; implemented recurring fingerprints, fixtures, and CI checks.

**Limits:** The ingestion result is verified for this case. Similar internal patterns recur inside RTS, but effectiveness and reuse outside RTS remain unobserved.

---

This publication is limited to this repository document. It does not authorize social posting, direct outreach, contracting, external execution, or publication on another surface.
