# Design & Function Translator v1

## Purpose

Translate vague visual and functional intent into an implementable, reviewable design brief without forcing the user to explain taste in professional design language.

The system must support a fast refinement loop:

1. accept rough requests, screenshots, sketches, and reference labels;
2. record likes, dislikes, confusion, urgency, and one-tap access needs;
3. infer the underlying intent;
4. convert that intent into design constraints and feature decisions;
5. propose what to keep, remove, defer, or clarify;
6. stop for human discussion before implementation.

## Core principle

Ambiguous language is valid input but invalid implementation authority.

Terms such as "premium", "modern", "sizzle", "friendly", or "simple" must be converted into observable choices before they can influence implementation.

## v1 scope

### Inputs

- free-form request text;
- domain, role, and target-user context;
- reference items represented by IDs, labels, notes, and optional source paths;
- per-reference reactions: like, dislike, neutral, confusing;
- explicit observations such as "too complex", "one-tap access", "this button is unclear";
- optional sensory adjustments using named axes and values from -1.0 to 1.0.

Image understanding and online reference discovery are adapters outside the v1 core. v1 accepts their normalized observations.

### Outputs

- inferred user goals;
- design constraints;
- required functions;
- removable or deferrable functions;
- unresolved questions;
- sensory profile;
- reference adoption ledger;
- human-readable Markdown brief;
- machine-readable JSON brief;
- status `AWAITING_HUMAN_DECISION`.

## Translation rules

### Example: "too complex"

Translate into candidates such as:

- reduce visible choices;
- flatten navigation depth;
- hide advanced settings;
- preserve a direct path to the primary action.

### Example: "I want one-tap access"

Translate into:

- identify the target action;
- verify actual frequency or urgency;
- evaluate fixed navigation, shortcut, recent-items entry, or contextual action;
- record the trade-off in visible space.

### Example: "this button makes no sense"

Translate into:

- label or icon ambiguity;
- missing affordance;
- unclear destination;
- candidate actions: relabel, add text, merge, move, or remove.

### Example: sensory language

Never pass a sensory word directly into implementation. Convert it through comparison, selection, and adjustment into explicit axes such as:

- gloss;
- warmth;
- texture;
- motion;
- density;
- spacing;
- contrast;
- playfulness;
- trust;
- luxury.

## Reference handling

Each reference must produce an adoption ledger:

- adopted structure;
- adopted interaction pattern;
- adopted visual quality;
- rejected element;
- rejection reason;
- source reference.

The system must not treat resemblance as authority. It extracts patterns and rebuilds them for the target purpose.

## Feature decisions

Every requested feature must be classified as one of:

- `KEEP` — required to satisfy the core purpose;
- `SIMPLIFY` — useful but currently too complex;
- `DEFER` — valuable later, not needed for the first usable version;
- `REMOVE` — does not support the stated purpose;
- `CLARIFY` — intent is not concrete enough to decide.

## Human boundary

The translator may infer, compare, and recommend. It may not:

- approve a final design;
- approve implementation;
- copy a reference product wholesale;
- convert unresolved sensory language directly into code;
- remove a requested capability without recording the reason;
- overwrite an existing brief.

## Acceptance criteria

1. Similar feedback produces deterministic design constraints.
2. "Too complex", "one-tap access", and "unclear button" produce concrete translation rules.
3. Reference reactions create an adoption ledger.
4. Sensory adjustments remain bounded from -1.0 to 1.0.
5. The output contains both JSON and Markdown.
6. The final state is always `AWAITING_HUMAN_DECISION`.
7. Existing output files are never overwritten.

## Deferred beyond v1

- direct image embedding and computer-vision extraction;
- live wireframe rendering;
- automatic online design discovery;
- design plugin orchestration;
- planned-vs-as-built screenshot comparison;
- UI consistency scanning across all screens;
- automatic PDF or slide generation;
- user-specific learned preference models across projects.
