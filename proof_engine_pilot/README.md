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

Original candidates, corrected revisions, internal assets, public-wording drafts, and review records remain preserved. This is not a model-weight update and does not manufacture human authorship for delegated AI judgments.

The current state is `PUBLISHED_TO_AUTHORIZED_REPOSITORY_DOCUMENT`. Any additional surface or distribution action requires a new explicit human authorization.
