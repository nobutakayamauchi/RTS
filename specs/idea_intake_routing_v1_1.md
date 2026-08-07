# RTS Idea Intake / Routing Layer
## V1.1 Scope Frozen — Emergency Activation Completion

**Status:** V1.0 FROZEN / V1.1 FROZEN / E2E VERIFIED  
**Parent:** RTS Design Knowledge Bridge / Dogfood Pipeline V1.0  
**Reason:** First real dogfood showed that V1.0 can complete a prepared request, but raw ideas still require a human to decide project, timing, missing prerequisites, and the correct V1.0 entry shape before the pipeline can start.

## 1. Purpose

V1.1 adds one thin activation layer before the frozen V1.0 pipeline.

```text
Raw Idea
  ↓
Classify
  ↓
Target Project / Component Proposal
  ↓
Timing Proposal: NOW / DEFER / CLARIFY
  ↓
Missing Parts
  ↓
FREEZER / Existing Context Matches
  ↓
Routing Proposal
  ↓
Human Approval
  ↓
V1.0-ready input
```

V1.1 does not modify V1.0 Definition of Done.

## 2. Incident that triggered V1.1

During first real-project selection, V1.0 could not be invoked directly from the raw idea without a human first preparing an Obsidian note and deciding where the idea belonged.

This is treated as a missing activation boundary, not a V1.0 pipeline failure.

V1.0 remains frozen and complete.

## 3. Input

Minimum input:

```json
{
  "idea": "free-form raw idea"
}
```

Optional context:

- `title`
- `project_id`
- `project_hint`
- `component_hint`
- `known_projects`
- `known_components`
- `freezer_matches`
- `constraints`
- `references`

The caller is not required to know an Obsidian destination.

## 4. Output

V1.1 produces a non-executing routing proposal containing:

- `idea_id`
- `classification`
- `target_project`
- `target_component`
- `timing`
- `missing_parts`
- `context_matches`
- `routing_action`
- `human_questions`
- `confidence`
- `v1_input`
- `status`

Allowed timing states:

- `NOW`
- `DEFER`
- `CLARIFY`

Allowed routing actions:

- `ROUTE_TO_V1`
- `FREEZE_FOR_LATER`
- `ASK_HUMAN`

## 5. Minimum classification set

- `FEATURE`
- `BUG`
- `DESIGN`
- `KNOWLEDGE`
- `REFERENCE`
- `UNKNOWN`

Classification is advisory. It must not trigger implementation.

## 6. Human Approval Boundary

V1.1 may create a proposal and a V1.0-ready payload, but it must not automatically:

- modify source projects
- write implementation code
- promote FREEZER knowledge
- approve a design
- begin implementation
- repair a defect

Default state:

```text
status = AWAITING_HUMAN_ROUTING_DECISION
human_decision_required = true
implementation_executed = false
```

## 7. V1.1 Definition of Done

1. Accept a raw idea without requiring a prepared Obsidian note.
2. Classify the idea.
3. Propose a target project and component when enough evidence exists.
4. Propose `NOW / DEFER / CLARIFY`.
5. Report missing prerequisites.
6. Preserve supplied FREEZER / existing-context matches.
7. Produce a human-readable routing report.
8. Never route, store, implement, or repair without human approval.
9. Produce a payload compatible with the existing V1.0 translation input contract.
10. Preserve the V1.0 Identity / Evidence / Approval boundaries.

These ten items are frozen for V1.1.

## 8. Stop Rule

The following are out of V1.1 scope:

- autonomous cross-project priority optimization
- automatic FREEZER promotion
- screenshot understanding
- autonomous repository-wide architectural planning
- automatic implementation
- automatic repair
- automatic approval

If useful, record these as Future Scope. Do not expand V1.1 DoD.

## 9. Real-project E2E verification

V1.1 was verified against the real Vlog Save / Export idea that triggered the missing activation-boundary discovery.

Observed route:

```text
Raw Idea
  ↓
classification = BUG
  ↓
target_project = vlog
  ↓
target_component = save-export
  ↓
timing = NOW
  ↓
routing_action = ROUTE_TO_V1
  ↓
status = AWAITING_HUMAN_ROUTING_DECISION
  ↓
Human APPROVE
  ↓
V1.0 Design E2E bundle generated
  ↓
status = HANDED_OFF_TO_V1_AWAITING_HUMAN_DECISION
```

Safety evidence:

```text
human_decision_recorded = true
implementation_executed = false
```

Regression result at freeze time:

```text
71 passed
```

The original operational failure — a raw idea not being able to activate V1.0 without manual Obsidian preparation and routing — is therefore considered closed for V1.1.

## 10. Future Scope discovered during V1.1 dogfood

The Vlog case contained both defect and design-change semantics. V1.1 intentionally keeps the frozen single-classification model.

Future versions may support multi-label classification such as:

```text
BUG + DESIGN_CHANGE
```

This is not required for V1.1 completion and must not reopen the frozen scope.

## 11. Freeze declaration

V1.1 is frozen after satisfying its ten-item Definition of Done, passing the full Knowledge Bridge regression suite, and completing the real-project Raw Idea → Routing → Human Approval → V1.0 handoff flow.

No additional feature is required to declare V1.1 complete.
