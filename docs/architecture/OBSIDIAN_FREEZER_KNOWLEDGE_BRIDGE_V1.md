# Obsidian → FREEZER Knowledge Bridge v1

Status: FORMAL SPECIFICATION
Decision: APPROVED FOR IMPLEMENTATION PLANNING
Scope: RTS knowledge intake, challenge, promotion, recall, and FREEZER integration

## 1. Purpose

Build a governed bridge that turns Obsidian notes, chat summaries, operation logs, test evidence, and reusable discoveries into structured knowledge that can be challenged, recalled, promoted, and finally admitted into RTS FREEZER without flattening unfinished thoughts into false specifications.

The bridge must make stored knowledge return to the correct development step. It is not a general-purpose note summarizer and it must not let an AI silently convert raw notes into build authority.

## 2. Current-system inventory

RTS FREEZER already provides:

- immutable candidate history;
- preliminary priority scoring;
- GitHub reuse and build-value assessment;
- implementation preflight;
- explicit human approval;
- WIP limit one;
- stale-assessment handling;
- recall and condition-watch modes;
- source references and dependencies.

Therefore this project must not rebuild FREEZER, GitHub reuse assessment, preflight, or human approval.

The missing layer is upstream of FREEZER:

1. capture heterogeneous notes with near-zero friction;
2. classify what the note actually is;
3. preserve raw wording and provenance;
4. connect it to existing decisions, specifications, failures, tests, and projects;
5. challenge it before promotion;
6. distinguish a useful reminder from a FREEZER candidate;
7. return relevant knowledge at the moment it is needed.

No current repository implementation for an Obsidian bridge was found. Obsidian is therefore treated as an external Markdown vault, not as the source of truth for governed RTS state.

## 3. Initial proposal before challenge

The initial idea was:

- define a folder structure in Obsidian;
- read recent notes every morning;
- find connections, contradictions, and high-leverage actions;
- place promising notes into a FREEZER queue;
- promote approved notes into FREEZER.

This is directionally correct but unsafe and too flat as written.

## 4. Devil's Advocate review

### 4.1 Failure: folder names become fake semantics

A note placed in `specs/` is not necessarily a specification. Manual filing can be wrong, stale, or aspirational.

Decision: folders are navigation hints only. Promotion depends on validated metadata and evidence, not path.

### 4.2 Failure: daily insight generation creates noise

A system that writes a new report every morning can create more unread material than it resolves.

Decision: daily output is conditional. It must be silent when there is no actionable connection, contradiction, stale decision, recall trigger, or human decision required.

### 4.3 Failure: AI converts discussion into authority

Summaries can erase uncertainty, alternatives, dissent, and the difference between “mentioned” and “decided.”

Decision: raw source text is immutable and linked. AI-generated normalized records are derivative artifacts with confidence and review state. They never receive build authority.

### 4.4 Failure: duplication with FREEZER

Creating a second candidate lifecycle in Obsidian would split authority and produce drift.

Decision: the bridge owns `CAPTURED → NORMALIZED → CHALLENGED → PROMOTION_READY`. FREEZER owns prioritization, assessment, preflight, approval, selection, execution state, and immutable candidate versions.

### 4.5 Failure: every useful note becomes a build candidate

Many notes are context, evidence, patterns, or reminders and should never enter the build queue.

Decision: promotion destinations are distinct:

- `RECALL_INDEX`: useful context returned at the right event;
- `PATTERN_LIBRARY`: reusable development/debug/operation pattern;
- `TEST_KNOWLEDGE`: regression or human-test knowledge;
- `PROJECT_CONTEXT`: project-local constraint or decision context;
- `FREEZER_CANDIDATE`: work that may deserve implementation;
- `ARCHIVE_ONLY`: preserved but not actively surfaced.

### 4.6 Failure: sensitive personal material leaks into GitHub

The vault may contain medical, employment, financial, personal, customer, or third-party information.

Decision: export is deny-by-default. The bridge stores hashes and local references where possible. Public-repository export requires explicit redaction status and human approval.

### 4.7 Failure: metadata maintenance becomes another SimCity

A large mandatory schema would make capture fail in practice.

Decision: capture requires only source, timestamp, and content. Classification metadata is added asynchronously. Human correction must be possible with one small edit.

### 4.8 Failure: contradiction detection treats evolution as error

A newer decision may intentionally supersede an older one.

Decision: contradictions are classified as `UNRESOLVED`, `INTENTIONAL_SUPERSESSION`, `SCOPE_DIFFERENCE`, or `FALSE_POSITIVE`. No automatic overwrite.

### 4.9 Failure: Obsidian availability becomes a runtime dependency

RTS must remain operable if the vault is unavailable, moved, or corrupted.

Decision: bridge reads and exports snapshots. FREEZER and RTS do not depend on a live Obsidian process.

## 5. Final architecture

```text
Raw sources
(chat, notes, operation logs, screenshots, test reports, GitHub)
        ↓
Obsidian Vault / external Markdown source
        ↓
Knowledge Intake Adapter
        ↓
Immutable Capture Store + source hash
        ↓
Normalizer and Classifier
        ↓
Connection / contradiction / duplication analysis
        ↓
Devil's Advocate Gate
        ↓
Promotion Router
  ├─ Recall Index
  ├─ Pattern Library
  ├─ Test Knowledge
  ├─ Project Context
  ├─ FREEZER Candidate Draft
  └─ Archive
        ↓
Human confirmation where authority, sensitivity, or ambiguity exists
        ↓
Existing RTS FREEZER gates
```

## 6. Source-of-truth boundaries

- Obsidian is the human-readable working knowledge surface.
- The immutable capture store preserves what was actually supplied.
- The bridge index is derived and rebuildable.
- GitHub remains source of truth for code and public versioned specifications.
- FREEZER remains source of truth for governed candidate state.
- Human approval remains the only route to build authority.

## 7. Minimal vault contract

The bridge supports any folder layout. The recommended layout is:

```text
00_inbox/
10_context/
20_problems/
30_decisions/
40_specs/
50_tests/
60_evidence/
70_patterns/
80_projects/
90_archive/
FREEZER_QUEUE/
LIMIT_DEVELOPMENT.md
```

Only `LIMIT_DEVELOPMENT.md` is semantically special. It describes current priorities, protected data rules, preferred AI behavior, and active project identifiers.

## 8. Knowledge record

Each normalized record contains:

```yaml
knowledge_id: KNO-YYYYMMDD-NNNN
source_type: chat | obsidian | operation_log | test | github | human
source_ref: local-or-public-reference
source_hash: sha256
captured_at: ISO-8601
knowledge_type: problem | intent | constraint | decision | spec | test | evidence | pattern | risk | idea
scope: private | project | shared | public
project_ids: []
status: captured | normalized | challenged | promotion_ready | promoted | superseded | archived
confidence: low | medium | high
sensitivity: public | internal | personal | restricted
summary: text
raw_excerpt: text
claims: []
open_questions: []
links_to_existing: []
contradictions: []
supersedes: []
promotion_destination: none | recall | pattern | test | project_context | freezer
human_review_required: true | false
```

The raw source remains separate and immutable.

## 9. Devil's Advocate gate

A record cannot become `promotion_ready` until the gate checks:

1. Is this an observation, proposal, or decision?
2. What evidence supports it?
3. What evidence would falsify it?
4. Does it contradict an approved or frozen item?
5. Is the contradiction real, scoped, or superseding?
6. Is this already implemented elsewhere?
7. Can an existing repository, architecture, schema, test, or workflow be reused?
8. Is this project-local or reusable?
9. Does it expose protected information?
10. What human decision remains?

For a `FREEZER_CANDIDATE`, the gate also requires:

- original problem;
- why it matters;
- preserved value;
- trigger and negative-trigger conditions;
- dependencies;
- source references;
- estimated effort range;
- proposed destination;
- explicit statement that build authority is not granted.

## 10. Event-based recall

Knowledge is surfaced on events, not only on a daily schedule.

Required events:

- `SPEC_DRAFTED`: return related decisions, constraints, prior specs, and contradictions;
- `DEVILS_ADVOCATE`: return counterexamples, failures, risks, and rejected alternatives;
- `ASSET_SEARCH`: return reusable structures and previous GitHub assessments;
- `FREEZER_INTAKE`: return promotion-ready candidate material and missing fields;
- `PREFLIGHT`: return hidden dependencies, migration risks, rollback evidence, and test knowledge;
- `UI_BOOTSTRAP`: return prior UI failures, navigation patterns, destructive tests, and human-only checks;
- `BUG_REPORTED`: return similar failures, previous fixes, and regression candidates;
- `RELEASE_GATE`: return unresolved risks, known limits, stale decisions, and required human tests;
- `RESUME_WORK`: return last approved state, unfinished decisions, and the next bounded action.

A daily or weekly brief is optional and must only report meaningful changes.

## 11. FREEZER adapter

The adapter creates a draft JSON compatible with the existing FREEZER item schema. It does not call `freezer.cli add` automatically.

Mapping:

- title ← normalized title;
- type ← routed type (`feature`, `research`, `architecture`, `process`, `risk`, or `product`);
- summary ← challenged summary;
- original_problem ← problem record;
- why_it_matters ← intent and impact;
- reason_frozen ← why work should not interrupt current WIP;
- preserved_value ← reusable findings and evidence;
- trigger_conditions / negative_triggers ← challenged conditions;
- dependencies ← linked governed items and projects;
- source_refs ← immutable source references;
- possible_destinations ← affected repositories or systems;
- estimated_hours ← bounded estimate;
- tags ← knowledge and project tags;
- build_authority ← always `NOT_APPROVED`;
- recall_mode ← `MANUAL` or `CONDITION_WATCH` based on explicit triggers.

Priority values are proposed with confidence notes but remain subject to FREEZER validation and human revision.

## 12. Privacy and export policy

- `personal` and `restricted` content is never exported to a public repository by default.
- Raw medical, employment, financial, customer, credential, and third-party records stay local unless explicitly redacted and approved.
- Public exports contain the minimum necessary summary and stable source hash, not raw private content.
- Secrets and credentials cause hard rejection.

## 13. v1 implementation boundary

Build now:

1. Markdown/YAML intake from a configured vault path;
2. immutable local capture records;
3. deterministic schema validation;
4. classifier interface with rule-based fallback;
5. Devil's Advocate checklist and result schema;
6. promotion router;
7. FREEZER draft exporter;
8. event-query CLI;
9. redaction and sensitivity gate;
10. tests using a synthetic vault.

Do not build in v1:

- Obsidian plugin;
- vector database;
- always-on daemon;
- automatic writes into FREEZER;
- automatic modification of original notes;
- autonomous implementation;
- cloud synchronization;
- full semantic graph UI;
- daily report generation when no event requires it.

## 14. Acceptance criteria

v1 is complete when:

1. A synthetic vault can be scanned without modifying it.
2. New or changed Markdown notes produce immutable capture records with hashes.
3. A note cannot be promoted based only on its folder location.
4. The system distinguishes observation, proposal, decision, specification, test, evidence, and reusable pattern.
5. Devil's Advocate output records supporting evidence, counterevidence, contradictions, and unresolved human decisions.
6. Sensitive content is blocked from public export.
7. A promotion-ready work item can produce a valid FREEZER draft with `NOT_APPROVED` authority.
8. No command automatically selects, approves, or starts a FREEZER item.
9. Event recall returns relevant knowledge for at least `SPEC_DRAFTED`, `BUG_REPORTED`, `FREEZER_INTAKE`, and `RESUME_WORK`.
10. Re-running intake without changes is idempotent.
11. Superseded decisions remain historically traceable.
12. The complete bridge can be disabled without breaking current FREEZER operation.

## 15. Decision

Adopt a thin, governed knowledge bridge rather than rebuilding FREEZER or creating a second lifecycle inside Obsidian.

The key rule is:

> Obsidian helps knowledge grow and return. The bridge challenges and routes it. FREEZER governs whether work enters the build queue.
