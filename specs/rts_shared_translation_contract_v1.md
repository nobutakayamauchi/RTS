# RTS Shared Translation Contract v1

## Purpose

Provide one stable boundary for Obsidian, the common UI, debugging links, FREEZER, and later document generators. Adapters may differ, but they must exchange the same request and translation brief shape.

## Compatibility

- Contract version: `1.0`
- Legacy Design & Function Translator inputs without `schema_version`, `request_id`, or `project_id` remain accepted.
- Missing identifiers are generated deterministically from the title and project context.
- Unknown input fields remain permitted so adapters can carry source-specific metadata without breaking v1.
- Output fields are additive. Existing semantic fields remain unchanged.

## Input boundary

Core fields:

- `schema_version`
- `request_id`
- `project_id`
- `title`
- `domain`
- `role`
- `target_user`
- `feedback`
- `goals`
- `constraints`
- `features`
- `references`
- `sensory_profile`
- `unresolved_questions`

The authoritative machine-readable definition is:

- `schemas/design_function_translation_input_v1.schema.json`

## Output boundary

The translation brief adds:

- stable `request_id` and `project_id`
- `missing_parts`
- `planned_structure.nodes`
- `planned_structure.edges`
- mandatory human approval state

The planned graph is intentionally small. It is a transport contract, not the final visualization engine.

Supported node types:

- request
- goal
- feature
- reference
- missing_part
- implementation_target
- approval

Supported edge types:

- clarifies
- implements
- depends_on
- inserts_into
- references
- blocks
- requires_approval

The authoritative machine-readable definition is:

- `schemas/design_function_translation_output_v1.schema.json`

## Safety boundary

Every generated brief must satisfy:

- `human_decision_required: true`
- `status: AWAITING_HUMAN_DECISION`
- a `requires_approval` edge in the planned graph

This contract does not authorize implementation, FREEZER promotion, publication, or destructive modification.

## Adapter rule

Obsidian, UI, and debugger adapters should translate native source data into the input contract and consume the output contract without embedding domain decisions in the adapter itself.

```text
source-specific input
  -> thin adapter
  -> shared input contract
  -> translator / council
  -> shared output contract
  -> source-specific presentation
```

## Completion criteria for action plan 2/7

- input and output schemas exist
- runtime validation executes before write
- stable IDs are emitted
- planned structure is emitted
- legacy input remains accepted
- approval boundary remains mandatory
