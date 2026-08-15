# Post Adapter v0

Status: `EVIDENCE-SAFE DRAFT TRANSFORMER / /human REQUIRED BEFORE EXTERNAL PUBLICATION`

Post Adapter v0 turns one evidence-bound development/update record into channel-shaped drafts for X, note, GitHub, and Instagram.

It does not log in to those services and does not publish anything.

**Important:** Post Adapter output is structured, evidence-safe draft material. It is not automatically considered natural public copy. Any external-facing X/note copy MUST pass the mandatory `/human` policy in `publication_bridge/HUMAN_STYLE_POLICY.md` before Publication Bridge may hand it to a platform.

## Why this v0 is thin

The useful core is:

```text
one source update
-> normalize
-> bind factual claims to declared evidence
-> apply channel policy
-> transform by channel
-> evidence review
-> APPROVED_FOR_COPY
-> /human rewrite + factual preservation check
-> APPROVED_FOR_HANDOFF
-> Publication Bridge
```

Direct posting, OAuth/token storage, scheduling, analytics, auto-replies, and account management are deliberately excluded.

## Source contract

Required top-level fields:

- `project_name`
- `update_type`
- `summary`
- `facts[]`
- `source_refs[]`
- `audience`
- `call_to_action`

A publishable fact has this minimum shape:

```json
{
  "claim": "A bounded factual statement.",
  "status": "VERIFIED",
  "source_ref": "source-001"
}
```

`source_ref` must match an `id` in `source_refs[]`.

Optional channel-shaping hints may be attached to a fact without changing its evidence state:

```json
{
  "priority": "critical",
  "must_keep": true
}
```

Supported priorities are:

```text
critical > high > normal > low
```

Facts without an explicit priority default to `normal`; `must_keep` defaults to `false`.

A fact that is unverified, or claims to be verified without a declared source binding, is not promoted into the publish-ready fact list. It becomes a human-review warning. If no verified facts survive, generation fails closed.

## Channel policy

Evidence binding and channel shaping are intentionally separate:

```text
Evidence Binding = what may be claimed
CHANNEL_POLICY = how much/where verified material initially goes
/human = how a real person would actually say it externally
```

The current X policy uses:

```text
CONTENT_BUDGET:
  unit = unicode_codepoints
  max_per_post = 260

FACT_PRIORITY:
  critical > high > normal > low

OVERFLOW_STRATEGY:
  thread

must_keep_fields:
  project_name / summary / call_to_action

max_thread_blocks:
  6
```

`260` is a conservative internal draft budget, not a permanent claim about X's exact platform counting rules. It belongs to the replaceable adapter policy and can change without rewriting the normalized source contract.

The shaping layer does **not** silently truncate or paraphrase a factual claim. If one required field or verified fact exceeds the configured per-post budget by itself, generation fails closed with a human-rewrite requirement.

## Mandatory `/human` boundary

`APPROVED_FOR_COPY` means only:

> the evidence-safe source is eligible to be rewritten into public copy.

It does **not** mean:

> safe to paste directly into X/note.

Before external handoff, run `/human` according to:

```text
publication_bridge/HUMAN_STYLE_POLICY.md
```

The final X/note text is then hash-bound into the bundle. Any later edit invalidates the `/human` pass and Publication Bridge fails closed.

## Run

From the repository root:

```bash
python -m post_adapter post_adapter/fixtures/example_update.json --out-dir /tmp/post-bundle
```

For a fully evidence-bound source:

```bash
python -m post_adapter clean_update.json \
  --out-dir /tmp/post-bundle \
  --review-state APPROVED_FOR_COPY
```

Then perform `/human` on the external drafts and record the completed pass:

```bash
python -m publication_bridge.human_gate /tmp/post-bundle \
  --reviewer /human \
  --evidence-preserved
```

Only then may Publication Bridge prepare X/note handoff controls.

## Output

```text
post-bundle/
├── manifest.json
├── source_summary.md
├── x.md
├── note.md
├── github.md
└── instagram.md
```

The manifest always records:

```json
"external_publication_performed": false
```

## Tests

```bash
python -m unittest discover -s tests -p 'test_post_adapter.py' -v
python -m unittest discover -s tests -p 'test_publication_bridge.py' -v
```

Post Adapter tests cover evidence/channel shaping. Publication Bridge tests cover the external `/human` gate, hash binding, user-only handoff, and fail-closed behavior.

## Extension boundary

A new output channel is a renderer registered against the normalized source contract. It must not require the source record to be rewritten around one platform.

Any external-facing channel added later inherits the same rule:

> Evidence-safe draft first. `/human` before public handoff. Never silently bypass the humanization boundary.
