# Post Adapter v0

Status: `HUMAN-REVIEWED DRAFT TRANSFORMER / NO EXTERNAL PUBLISHING`

Post Adapter v0 turns one evidence-bound development/update record into channel-shaped drafts for X, note, GitHub, and Instagram.

It does not log in to those services and does not publish anything.

## Why this v0 is thin

The useful core is:

```text
one source update
-> normalize
-> bind factual claims to declared evidence
-> apply channel policy
-> transform by channel
-> human review
-> approved-for-copy output
```

Direct posting, OAuth/token storage, scheduling, analytics, auto-replies, and account management are deliberately excluded. They are not necessary to prove whether the transformation layer saves work and preserves claim quality.

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
CHANNEL_POLICY = how that verified content is shaped for one channel
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

The X primary post reserves room for project/summary, the highest-priority facts that fit, and the CTA. Remaining verified facts move to explicit continuation blocks.

The shaping layer does **not** silently truncate or paraphrase a factual claim. If one required field or verified fact exceeds the configured per-post budget by itself, generation fails closed with a human-rewrite requirement.

## Run

From the repository root:

```bash
python -m post_adapter post_adapter/fixtures/example_update.json --out-dir /tmp/post-bundle
```

The original included dogfood fixture intentionally contains one unsupported completion claim. The expected result is a generated bundle with `REVIEW_REQUIRED`, while the unsupported claim is excluded from the publish-ready portion of each draft and retained as a warning for the reviewer.

A production-shaped BridgePatch fixture is also retained at:

```text
post_adapter/fixtures/bridgepatch_launch_20260815.json
```

It verifies the X budget/priority/thread path without external publication.

For a fully evidence-bound source, a human may explicitly record:

```bash
python -m post_adapter clean_update.json \
  --out-dir /tmp/post-bundle \
  --review-state APPROVED_FOR_COPY
```

`APPROVED_FOR_COPY` is rejected when verification warnings remain.

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

and now also records the applicable channel policy and X shaping metrics.

## Tests

```bash
python -m unittest discover -s tests -p 'test_post_adapter.py' -v
```

The tests cover:

- four distinct default channel outputs;
- no external-publication state;
- unsupported-claim exclusion;
- fail-closed missing evidence;
- blocking `APPROVED_FOR_COPY` when warnings remain;
- clean human approval state;
- replaceable channel-policy manifest;
- BridgePatch two-post dogfood under budget;
- exact preservation of all BridgePatch verified claims;
- oversized single-claim fail-closed behavior;
- invalid fact-priority fail-closed behavior;
- extension with a fifth adapter without changing the normalized source contract.

## Extension boundary

A new output channel is a renderer registered against the normalized source contract. It must not require the source record to be rewritten around one platform.

The v0 public boundary remains:

> Adapt content; do not publish it.
