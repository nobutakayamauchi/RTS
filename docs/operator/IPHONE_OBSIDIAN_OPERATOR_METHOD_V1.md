# iPhone-Only Obsidian Operator Method v1

## Purpose

This method lets an operator use only an iPhone and Obsidian as a human-facing capture, review, and resume surface without making Obsidian authoritative for RTS state.

The method preserves the RTS boundaries for append-only history, WIP=1, Assessment, Preflight, Human Gate, external-action authority, and reconstruction.

```text
Obsidian capture
→ human distillation
→ GitHub Issue proposal
→ RTS-AGE inspection and normalization
→ RTS governance gates
→ read-only mobile status back to Obsidian
```

Obsidian is a cockpit, not the RTS ledger.

## Responsibility split

### Obsidian

Obsidian may hold:

- rough ideas;
- hypotheses;
- incomplete specifications;
- private working notes;
- public-safe proposal summaries;
- a derived read-only RTS status view.

Obsidian does not hold authoritative RTS approval, execution authority, or lifecycle state.

### RTS-AGE

RTS-AGE may inspect and normalize a submitted proposal and prepare a bounded RTS-facing proposal. It must not treat an Issue, note property, shortcut action, or copied instruction as approval.

### RTS

RTS remains authoritative for:

- FREEZER items and versions;
- Build Assessments;
- Implementation Preflights;
- human-review evidence;
- selected and in-progress state;
- execution evidence and checkpoints;
- current position and next gates.

## Required Obsidian folders

Create the following folders in the operator Vault:

```text
System/
└── RTS_Bridge/
    ├── 00_Inbox/
    ├── 10_Staging/
    ├── 20_Submitted/
    ├── 80_Generated_ReadOnly/
    ├── 90_Templates/
    └── 99_Quarantine/
```

- `00_Inbox`: quick capture and voice-dictated notes.
- `10_Staging`: notes being reduced to a bounded proposal.
- `20_Submitted`: local operator references to proposals already submitted.
- `80_Generated_ReadOnly`: derived RTS status notes. Human edits are not authoritative.
- `90_Templates`: local note templates.
- `99_Quarantine`: material that is private, unsafe, ambiguous, or not ready to submit.

## Local operator states

The following states are operator aids only. They are not RTS lifecycle states.

```text
CAPTURED
STAGED
PUBLIC_SAFE
SUBMITTED
RETURNED_FOR_REVISION
ACCEPTED_AS_PROPOSAL
REJECTED
QUARANTINED
```

## Method

### 1. CAPTURE

Write the idea in `00_Inbox` without forcing it into an RTS schema.

Do not interrupt current WIP merely because a new note exists.

### 2. DISTILL

Move a useful candidate to `10_Staging` and produce a short public-safe summary containing:

- problem;
- why it matters;
- preserved value;
- likely dependencies;
- known risks;
- trigger conditions;
- stop conditions.

The summary should normally remain below 1,500 characters for the v1 Issue route.

### 3. PRIVACY CHECK

Stop and move the note to `99_Quarantine` when it contains or may contain:

- credentials, API keys, tokens, or secrets;
- customer or third-party personal data;
- medical, employment, legal, or government-identifier source material;
- private messages, DM bodies, recordings, or raw transcripts;
- private repository bodies;
- provider payloads or tool arguments;
- information whose publication authority is unclear.

Only a separately written public-safe summary may continue.

### 4. SUBMIT

Use the iOS Share Sheet shortcut named `RTSへ提案` on the selected public-safe summary.

The shortcut must:

1. accept selected text only;
2. ask the operator to confirm `公開可能` or `非公開・保留`;
3. stop on `非公開・保留`;
4. collect a short title and proposal category;
5. URL-encode the title and body;
6. open the repository Issue creation page using the `obsidian-intake.md` template;
7. require the operator to read and manually submit the Issue.

The shortcut must not store a GitHub write token and must not call the GitHub write API.

Issue creation is proposal submission only. It does not create:

- a FREEZER item;
- build authority;
- a selection decision;
- an execution authorization;
- a customer action;
- a publication decision.

### 5. GOVERN

A submitted Issue may be reviewed by RTS-AGE and converted into a bounded proposal, but normal RTS gates remain mandatory:

```text
proposal review
→ FREEZER registration or rejection
→ Build Assessment
→ Implementation Preflight
→ explicit human approval
→ WIP=1 selection
```

No Obsidian property, Issue checkbox, label, shortcut result, or generated summary may bypass these gates.

### 6. RESUME

Use the iOS shortcut named `RTS現在地を更新` before beginning work and after an RTS state change.

The shortcut must:

1. fetch `docs/status/RTS_MOBILE_STATUS.json` by HTTPS GET only;
2. reject an unknown schema version;
3. format a compact Japanese Markdown status note;
4. write it to `System/RTS_Bridge/80_Generated_ReadOnly/RTS_Current_Position.md` through an Obsidian URI;
5. overwrite only that generated file;
6. include the source path and fetch time;
7. state that the note is derived and non-authoritative.

The operator must read:

- current state;
- next gate;
- wait or block condition;
- WIP limit;
- permitted actions;
- prohibited actions.

## Shortcut specification: RTSへ提案

Recommended Shortcuts actions:

```text
Receive Text from Share Sheet
→ Choose from Menu: 公開可能 / 非公開・保留
→ Stop Shortcut when non-public
→ Ask for Input: title
→ Choose from Menu: category
→ Trim Text
→ Reject empty text
→ Reject text over 1,500 characters
→ URL Encode title and body
→ Open URL: GitHub Issue creation page
```

The generated body should begin with:

```text
PROPOSAL_ONLY
UNVERIFIED
NO_BUILD_AUTHORITY
HUMAN_REVIEW_REQUIRED
```

## Shortcut specification: RTS現在地を更新

Recommended Shortcuts actions:

```text
Get Contents of URL using GET
→ Get Dictionary from Input
→ Check schema_version
→ Get Dictionary Values
→ Build Markdown
→ URL Encode Markdown
→ Open Obsidian URI with overwrite and silent flags
```

No POST, PUT, PATCH, DELETE, shell, provider call, polling, or background monitoring is permitted in v1.

## Source-of-truth rule

`docs/status/RTS_MOBILE_STATUS.json` is a derived mobile projection. Its `source_of_truth` field identifies the authoritative current-position record.

If the mobile file disagrees with the authoritative source, the authoritative source wins and the mobile file is stale.

The generated Obsidian note is a cache of the mobile projection, not evidence of RTS state.

## Prohibited v1 integrations

The following are out of scope:

- making the RTS repository an Obsidian Vault;
- Obsidian Git synchronization of RTS authoritative files;
- Working Copy auto-commit or auto-push;
- storing GitHub write credentials in an iOS shortcut;
- automatic Issue submission;
- automatic FREEZER registration;
- automatic approval, selection, PR creation, merge, execution, publication, or follow-up;
- VPS, Obsidian Headless, scheduled polling, or always-on monitoring;
- full-Vault export;
- reverse synchronization from Obsidian into RTS authoritative files.

## Start-of-work checklist

- Refresh the mobile status.
- Confirm the current state and next gate.
- Confirm that the intended work is permitted now.
- Confirm WIP=1 remains satisfied.
- Do not reinterpret waiting as permission to advance the blocked path.

## End-of-work checklist

- Record only the relevant Issue or PR reference in the local note.
- Record `decided`, `unresolved`, and `next gate`.
- Refresh the mobile status after the authoritative RTS state changes.
- Do not copy full private conversations, raw execution payloads, or repository ledgers into Obsidian.

## Completion criteria

This method is complete when:

- an iPhone can open a prefilled proposal Issue without a stored write token;
- a human must review and submit the Issue;
- unsafe or ambiguous source material is stopped before submission;
- an iPhone can render the mobile status into a read-only Obsidian note;
- Obsidian cannot create or expand RTS authority;
- Assessment, Preflight, Human Gate, and WIP=1 remain mandatory;
- RTS remains verifiable and reconstructable without Obsidian.
