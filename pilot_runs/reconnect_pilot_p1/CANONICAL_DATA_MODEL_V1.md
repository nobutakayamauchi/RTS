# Canonical Data Model v1

## Record types

1. **SourceRecord** — source ID, type, repository, ref, path/PR, fingerprint, visibility
2. **ActivityRecord** — exact observed action, actor class, time, source links
3. **AchievementCandidate** — bounded claim, status, confidence, evidence IDs
4. **EvidenceClaim** — claim fragment, evidence label, source links, reasoning, conflicts
5. **ContributionMap** — human, AI, collaborator, OSS/tool contributions and uncertainty
6. **ValueAssessment** — audience, problem addressed, value mechanism, limits
7. **OpportunityCandidate** — possible audience or use, not an automatic recommendation
8. **HumanDecision** — approve/revise/reject/redact/expire, exact target fingerprint
9. **OutputAsset** — approved-source draft, audience, disclosure class, NOT_PUBLISHED
10. **MarketSignal** — later manual response, source, interpretation, confidence

## Evidence labels

VERIFIED / INFERRED / SELF_REPORTED / UNVERIFIED / CONFLICTED

## Contribution dimensions

Problem framing, goal selection, constraints, architecture, specification, AI direction, acceptance criteria, review, rejection, integration, recovery, approval, implementation, inherited OSS/tool behavior.

## Required invariants

- IDs are unique and stable.
- Claims link to one or more SourceRecords.
- VERIFIED claims cannot rely solely on generated prose.
- HumanDecision is append-only and target-fingerprint-bound.
- OutputAsset remains NOT_PUBLISHED until a separate human action.
- Sensitive data is rejected before persistence.
- Unobserved capability is never encoded as lack of capability.
