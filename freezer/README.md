# RTS FREEZER v1

RTS FREEZER is a versioned queue for valuable work that should not interrupt the current build.

It preserves feature ideas, research targets, products, architectures, processes, and risks as immutable versions. Each completed implementation cycle can re-score every current candidate, show the leading options, and leave final selection to a human.

## Operating rule

1. Capture every valuable candidate instead of inserting it into work in progress.
2. Preserve raw score dimensions and reasons, not only one final score.
3. Rebuild the complete ranking after a build finishes or a major condition changes.
4. Show the top candidates and their reasons.
5. Run an implementation preflight before selecting any candidate.
6. Require explicit human approval.
7. Pull one item only. The default work-in-progress limit is `1`.
8. Feed discoveries and follow-up ideas back into FREEZER, then repeat.

FREEZER never starts implementation automatically.

## Storage model

```text
freezer/
├── config.json
├── schemas/
│   ├── item.schema.json
│   └── preflight.schema.json
├── templates/preflight_input.json
├── items/RTS-FRZ-000001/
│   ├── v001.json
│   └── current.json
├── preflights/RTS-FRZ-000001/
│   ├── pf001.json
│   └── current.json
├── index/
│   ├── items.json
│   └── priority.json
└── manifests/manifest.sha256
```

- `vNNN.json` files are immutable candidate history.
- `pfNNN.json` files are immutable implementation-preflight history.
- `current.json` points to the current version in each history.
- Indexes are derived and may be rebuilt.
- Raw priority dimensions remain in each item, so changing score weights does not rewrite history.
- The manifest covers the FREEZER source, configuration, indexes, schemas, items, and preflights.

## Priority model

Benefit fields:

- impact
- urgency
- strategic fit
- readiness
- revenue value
- dependency value
- risk reduction
- confidence

Cost fields:

- effort
- uncertainty

Each dimension is scored from 0 to 5. Cost dimensions are inverted during calculation. Weights live in `freezer/config.json`.

A score is a recommendation, not implementation authority.

## Implementation preflight: the ground survey

A high-ranked candidate is not assumed to be a small or isolated change. Before selection, the preflight inspects the ground under the proposed work:

- affected boundaries
- existing assumptions
- data migration
- external interfaces
- approval changes
- public documents and claims
- regression tests
- hidden dependencies
- rollback boundary
- completion conditions
- decomposition requirement
- major risks

The preflight outcome is one of:

- `PASS`: bounded work may proceed to the human gate.
- `DECOMPOSE_REQUIRED`: create child candidates and do not start the parent.
- `BLOCKED`: a known condition prevents implementation.
- `RESEARCH_REQUIRED`: important unknowns must be resolved first.

A preflight stores a fingerprint of the substantive implementation plan. Status, approval, timestamps, priority scores, effort estimates, tags, and recall metadata may change without invalidating it, so the queue can be re-ranked normally. Changes to scope, preserved value, safety exclusions, dependencies, sources, or intended destination make the preflight `STALE`, and selection is blocked until the ground survey is run again.

## Commands

Run from the repository root:

```bash
python -m freezer.cli reindex
python -m freezer.cli list
python -m freezer.cli show RTS-FRZ-000001
python -m freezer.cli history RTS-FRZ-000001
python -m freezer.cli recall RTS-FRZ-000001
python -m freezer.cli verify
```

Add a new candidate from a JSON document:

```bash
python -m freezer.cli add --input /path/to/new_item.json
```

The input may omit `item_id`, `version`, `created_at`, and `updated_at`; FREEZER assigns them.

Append a revision without overwriting history:

```bash
python -m freezer.cli revise RTS-FRZ-000001 --input /path/to/changes.json
```

The revision file may contain only changed fields. It cannot replace `item_id`, `version`, or `created_at`.

Create and inspect a ground-survey preflight:

```bash
cp freezer/templates/preflight_input.json /tmp/preflight.json
python -m freezer.preflight create RTS-FRZ-000001 --input /tmp/preflight.json
python -m freezer.preflight status RTS-FRZ-000001
python -m freezer.preflight show RTS-FRZ-000001
python -m freezer.preflight history RTS-FRZ-000001
python -m freezer.cli reindex
```

## Selection boundary

The derived priority list may recommend the top three candidates. It does not change an item to `SELECTED`, does not start code generation, and does not authorize external actions.

Before implementation:

1. Reindex all current candidates.
2. Inspect the top candidates and dependencies.
3. Complete a current implementation preflight.
4. If the result is `DECOMPOSE_REQUIRED`, return the child candidates to FREEZER and rank again.
5. Confirm the real-world constraints and rollback boundary.
6. Obtain explicit human approval for one candidate.
7. Revise that item to `SELECTED`, then begin work.

`SELECTED` and `IN_PROGRESS` require both:

- a current `PASS` preflight matching the substantive candidate fingerprint
- `build_authority: APPROVED`

The work-in-progress limit remains one.

## Seed item

`RTS-FRZ-000001` seals the Governed Adaptive Memory Layer discussed in July 2026. Its implementation remains unapproved and frozen until its trigger conditions are met. It does not yet have a passing implementation preflight because it is not being selected for construction.
