# RTS FREEZER v1

RTS FREEZER is a versioned queue for valuable work that should not interrupt the current build.

It preserves feature ideas, research targets, products, architectures, processes, and risks as immutable versions. After each completed implementation cycle, FREEZER re-scores all current candidates, measures build value and GitHub reuse potential, inspects the selected candidate's implementation ground, and leaves final selection to a human.

## Operating loop

1. Capture every valuable candidate instead of inserting it into work in progress.
2. Preserve raw priority dimensions and reasons, not only one final score.
3. Rebuild the complete preliminary ranking after a build finishes or a major condition changes.
4. Run a GitHub reuse and build-value assessment on the leading candidates.
5. Rebuild the combined build ranking.
6. Run an implementation preflight on the highest candidate that still looks worth building.
7. Decompose, research, block, or reject the candidate when the evidence says not to build it as-is.
8. Require explicit human approval.
9. Pull one item only. The default work-in-progress limit is `1`.
10. Feed discoveries and follow-up ideas back into FREEZER, then repeat.

FREEZER never starts implementation automatically.

## Storage model

```text
freezer/
├── config.json
├── schemas/
│   ├── item.schema.json
│   ├── preflight.schema.json
│   └── build_assessment.schema.json
├── templates/
│   ├── preflight_input.json
│   └── build_assessment_input.json
├── items/RTS-FRZ-000001/
│   ├── v001.json
│   └── current.json
├── assessments/RTS-FRZ-000002/
│   ├── ba001.json
│   └── current.json
├── preflights/RTS-FRZ-000002/
│   ├── pf001.json
│   └── current.json
├── index/
│   ├── items.json
│   ├── priority.json
│   └── build_priority.json
└── manifests/manifest.sha256
```

- `vNNN.json` files are immutable candidate history.
- `baNNN.json` files are immutable GitHub reuse and build-value assessments.
- `pfNNN.json` files are immutable implementation-preflight history.
- `current.json` points to the latest version in each history.
- Indexes are derived and may be rebuilt.
- Raw dimensions remain stored, so weights can change without rewriting history.
- The manifest covers FREEZER source, configuration, indexes, schemas, items, assessments, and preflights.

## Preliminary priority

The original FREEZER priority model remains the fast first pass.

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

This score answers: **which candidates deserve closer inspection?** It is not enough to authorize construction.

## GitHub reuse and build-value assessment

Before a candidate reaches implementation preflight, inspect GitHub and record what can shorten or reshape the build.

The survey records:

- repositories and search terms inspected
- reusable code, schemas, tests, workflows, documentation, data, and design material
- exact repository, path, and ref
- direct reuse, adaptation, reference-only, or no reuse
- licensing status
- estimated hours saved
- search gaps and uncertainty

The build assessment also records:

- expected impact
- strategic fit
- revenue leverage
- risk reduction
- recurrence across future work
- confidence in the evidence
- from-scratch implementation hours
- integration hours
- validation hours
- unknown-work buffer

Derived values are deterministic:

```text
reuse_hours_saved = min(sum(reusable asset savings), from_scratch_hours)
net_hours = from_scratch_hours - reuse_hours_saved
            + integration_hours + validation_hours + unknown_buffer_hours
implementation_efficiency = from_scratch_hours / net_hours
```

The decision score combines:

- 55% expected benefit
- 30% net implementation cost
- 15% reuse leverage

Recommendations:

- `BUILD_NOW`: strong current value and acceptable cost
- `BUILD_NEXT`: valuable, but another candidate may be better now
- `DEFER`: preserve it, but current cost-effectiveness is weak
- `RESEARCH_REQUIRED`: repository scan or evidence confidence is insufficient
- `REJECT`: current evidence does not justify implementation

A recommendation is evidence-backed advice, not authority.

### Combined ranking

`build_priority.json` combines the preliminary priority score and the current build assessment:

```text
combined ranking = 35% preliminary priority + 65% build decision score
```

A missing, stale, or invalid assessment receives only the preliminary 35% contribution and is marked `ASSESSMENT_REQUIRED`.

## Implementation preflight: the ground survey

A high-ranked candidate is not assumed to be small or isolated. The preflight inspects:

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

Outcomes:

- `PASS`: bounded work may proceed to the human gate.
- `DECOMPOSE_REQUIRED`: create child candidates and do not start the parent.
- `BLOCKED`: a known condition prevents implementation.
- `RESEARCH_REQUIRED`: important unknowns must be resolved first.

A substantive plan revision makes the old assessment or preflight `STALE`. Ordinary status changes and preliminary reranking do not.

## Selection boundary

Before implementation:

1. Reindex preliminary priority.
2. Inspect the top candidates.
3. Search GitHub and create a current build assessment.
4. Reindex the combined build ranking.
5. Choose the strongest `BUILD_NOW` candidate.
6. Complete a current implementation preflight.
7. If decomposition or research is required, return the result to FREEZER and rank again.
8. Confirm real-world constraints and rollback boundary.
9. Obtain explicit human approval.
10. Revise one item to `SELECTED`, then begin work.

Repository verification rejects a current `SELECTED` or `IN_PROGRESS` item without a current `BUILD_NOW` assessment. The existing Preflight gate, explicit `build_authority: APPROVED`, and WIP limit one remain in force.

## Commands

Run from the repository root.

### Candidate queue

```bash
python -m freezer.cli reindex
python -m freezer.cli list
python -m freezer.cli show RTS-FRZ-000001
python -m freezer.cli history RTS-FRZ-000001
python -m freezer.cli recall RTS-FRZ-000001
python -m freezer.cli verify
```

Add or revise candidates:

```bash
python -m freezer.cli add --input /path/to/new_item.json
python -m freezer.cli revise RTS-FRZ-000001 --input /path/to/changes.json
```

### GitHub reuse and build assessment

```bash
cp freezer/templates/build_assessment_input.json /tmp/build-assessment.json
python -m freezer.build_assessment create RTS-FRZ-000001 --input /tmp/build-assessment.json
python -m freezer.build_assessment status RTS-FRZ-000001
python -m freezer.build_assessment show RTS-FRZ-000001
python -m freezer.build_assessment history RTS-FRZ-000001
python -m freezer.build_assessment reindex
python -m freezer.build_assessment list
python -m freezer.build_assessment verify
```

Show the full selection gate:

```bash
python -m freezer.build_assessment gate RTS-FRZ-000001
```

The gate reports the build assessment, Preflight, human authority, item state, and whether the candidate is ready for selection. It does not change state or begin implementation.

### Implementation preflight

```bash
cp freezer/templates/preflight_input.json /tmp/preflight.json
python -m freezer.preflight create RTS-FRZ-000001 --input /tmp/preflight.json
python -m freezer.preflight status RTS-FRZ-000001
python -m freezer.preflight show RTS-FRZ-000001
python -m freezer.preflight history RTS-FRZ-000001
```

## Seed records

- `RTS-FRZ-000001` preserves the Governed Adaptive Memory Layer. It remains `FROZEN`, `NOT_APPROVED`, and unassessed until its trigger conditions are met.
- `RTS-FRZ-000002` records the GitHub Reuse and Build Value Assessment implemented in July 2026. Its assessment found a `75.37` decision score, `10.0` estimated net hours from a `16.0` hour from-scratch baseline, `10.0` reusable hours, and a `BUILD_NOW` recommendation. Its implementation preflight passed and the item is recorded as `COMPLETED`.
