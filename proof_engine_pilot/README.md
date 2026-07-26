# Proof Engine Pilot v1

A deterministic, standard-library-only minimum vertical slice for evidence-backed achievement discovery.

## Candidate-run commands

```bash
python -m proof_engine_pilot.cli generate
python -m proof_engine_pilot.cli verify
python -m proof_engine_pilot.cli summary
python -m proof_engine_pilot.cli review-template
```

## Human-review commands

```bash
python -m proof_engine_pilot.review_cli verify
python -m proof_engine_pilot.review_cli summary
python -m proof_engine_pilot.review_cli effective
```

## Review-derived learning commands

```bash
python -m proof_engine_pilot.learning_cli verify
python -m proof_engine_pilot.learning_cli summary
python -m proof_engine_pilot.learning_cli replay
python -m proof_engine_pilot.learning_cli preflight path/to/future_candidate.json
```

Round 0001 stores seven accepted originals and five original-to-revision correction pairs as a repository-local learning dataset. Six active rules provide `SUGGEST_ONLY` factuality and classification preflight for candidate runs after `PROOF-ENGINE-P3-RUN-0001`.

## Six-part internal asset commands

```bash
python -m proof_engine_pilot.asset_cli generate
python -m proof_engine_pilot.asset_cli verify
python -m proof_engine_pilot.asset_cli summary
python -m proof_engine_pilot.asset_cli review-template
```

The twelve effective reviewed candidates are consolidated exactly once into six internal asset drafts:

1. Governed Loop Engine
2. WIP=1 and Human-Gated Delivery
3. Append-Only Human Review and Integrity Checks
4. Promotion Application Preview
5. Adaptive Governance Compiler and Audit Remediation
6. Conversation-to-Seed Project Ingestion

## Internal asset review commands

```bash
python -m proof_engine_pilot.asset_review_cli verify
python -m proof_engine_pilot.asset_review_cli summary
python -m proof_engine_pilot.asset_review_cli effective
```

All six internal assets were reviewed against factuality, contribution separation, non-overlap, privacy, and internal-source readiness. They are approved only as sources for the public-wording draft stage.

## Audience-facing wording draft commands

```bash
python -m proof_engine_pilot.public_wording_cli generate
python -m proof_engine_pilot.public_wording_cli render-markdown
python -m proof_engine_pilot.public_wording_cli verify
python -m proof_engine_pilot.public_wording_cli summary
python -m proof_engine_pilot.public_wording_cli review-template
```

The six approved internal sources are translated into English audience-facing wording with a headline, summary, value explanation, evidence note, human and AI-tool attribution, and explicit limits. Every draft passes the active review-learning preflight and remains `PUBLICATION_REVIEW_REQUIRED / NOT_PUBLISHED`.

## Delegated publication wording review commands

```bash
python -m proof_engine_pilot.publication_review_cli verify
python -m proof_engine_pilot.publication_review_cli summary
python -m proof_engine_pilot.publication_review_cli effective
python -m proof_engine_pilot.publication_review_cli release-template
```

Publication review round 0001 records the distinction between the human project owner's explicit delegation and the AI assistant's wording judgment. Three originals are accepted unchanged. Three originals remain preserved while revised versions tighten scope or reader clarity:

- `WORDING-002-R1` explicitly limits WIP=1 to the governed pilot in the headline;
- `WORDING-003-R1` replaces unclear stale-expiry phrasing with expired-or-stale decision language;
- `WORDING-005-R1` describes governance as derived from declared change and authority context rather than exact risk measurement.

## Bounded repository publication release

```bash
python -m proof_engine_pilot.release_cli verify
python -m proof_engine_pilot.release_cli summary
```

The project owner authorized exactly one public release surface:

```text
docs/portfolio/RTS_EVIDENCE_BACKED_PROJECT_OUTPUTS.md
```

The committed document is generated from the six effective reviewed wordings and is bound to an exact content fingerprint. The release authorization permits publication to this public RTS repository document only. It does not permit a root README link, social posting, direct outreach, contracts, provider execution, adjacent-repository writes, or automatic republication.

## Sequential cross-repository validation

```bash
python -m proof_engine_pilot.cross_repo_cli verify
python -m proof_engine_pilot.cross_repo_cli summary
python -m proof_engine_pilot.cross_repo_cli review-template
```

Campaign 0001 runs three bounded read-only validation rounds in order:

1. `seminar-compass` as a generalization test for a conventional learning product;
2. `RTS-minicompany` as a private business-repository test using metadata-only evidence;
3. `rts-video-flow` as a negative control for a frozen, untested scaffold.

The campaign produces sixteen review-required candidates and withholds five unsupported claims. Unmerged Seminar Compass PRs remain in the source snapshot but are ineligible as evidence. The private MiniCompany source copies no customer payload. The video-flow round records only the scaffold and freeze state and explicitly withholds end-to-end, accuracy, and production-readiness claims.

## Round 2 cross-repository review

```bash
python -m proof_engine_pilot.cross_repo_review_cli verify-round-2
python -m proof_engine_pilot.cross_repo_review_cli summary-round-2
python -m proof_engine_pilot.cross_repo_review_cli effective-round-2
python -m proof_engine_pilot.cross_repo_review_cli round-3-template
```

The project owner explicitly confirmed the `seminar-compass` review. Five original candidates were approved. `SC-006` was preserved, marked `REVISE`, reclassified from `AUDIT_REMEDIATION_BYPRODUCT` to `PROCESS_BYPRODUCT`, and approved as `SC-006-R1`.

Round 2 records an 83.3% first-pass approval rate and a 16.7% revision rate. The higher first-pass approval rate than the original RTS round is recorded only as `POSITIVE_SIGNAL_NOT_PROOF`, because the repository type and candidate count differ.

The correction reinforces existing artifact-kind rule `REVIEW-RULE-002`; it does not activate a new rule or grant automatic correction or approval authority. Round 3 remains a separate human review.

No target repository is modified. Publication, outreach, provider execution, contracts, automatic rewriting, and automatic approval remain unauthorized.

Original candidates, corrected revisions, internal assets, public-wording drafts, review records, and source snapshots remain preserved. This is not a model-weight update and does not manufacture human authorship for delegated AI judgments.

The current review state is `ROUND_2_COMPLETE_ROUND_3_REVIEW_REQUIRED / NOT_PUBLISHED`.
