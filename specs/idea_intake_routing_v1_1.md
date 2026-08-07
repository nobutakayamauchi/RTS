# RTS Idea Intake / Routing Layer
## V1.1 Scope Frozen — Emergency Activation Completion

**Status:** V1.0 FROZEN / V1.1 IMPLEMENTATION IN PROGRESS  
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
