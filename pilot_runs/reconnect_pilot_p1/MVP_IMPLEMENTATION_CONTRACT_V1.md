# MVP Implementation Contract v1

## Contract ID

`PROOF-ENGINE-P3-MIN-VERTICAL-SLICE-V1`

## Fixed source boundary

- Repository: `nobutakayamauchi/RTS`
- Evidence set: merged PRs `#242` through `#261`, their changed files, review findings, linked tests, and completion records
- Visibility: public repository evidence only
- No other repository, issue set, email, private document, or provider input

## Processing order

1. Register exact PR/source fingerprints
2. Extract observed activities
3. Generate achievement candidates
4. Link exact evidence
5. Assign evidence label
6. Build contribution map
7. Translate value for the first audience
8. Run exaggeration/conflict checks
9. Produce human-review queue
10. Generate one output draft from approved records only
11. Save manifest and checkpoint

## Required outputs

- minimum 10 AchievementCandidates
- evidence link for every candidate
- ContributionMap for every candidate
- ValueAssessment for every candidate
- evidence-status summary
- human decision template
- one portfolio/report draft marked NOT_PUBLISHED
- deterministic run manifest and checkpoint

## Completion gate

At least 10 candidates are generated; all have exact evidence; at least 3 are judged by the human as previously under-recognized; unsupported inflation is rejectable; one approved draft is created; no external action occurs.

## Explicit exclusions

Automatic publication, outreach, contracts, ranking, provider calls, private data, multi-repository ingestion, matching, Support Fit, Talent DB, DNS Wave, sales automation, and outcome guarantees.

## Target implementation recommendation

For the first engine test, use a repository-local, standard-library-first package in RTS with read-only GitHub evidence fixtures. This recommendation is not write authority and requires the next human gate.

## Rollback/freeze point

The P1 specification commit. P3 can be frozen without changing P0/P1 records.
