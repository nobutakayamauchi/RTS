# X Article Engine Plain v0 — Reverse Engineering Record

Status: DRAFT / DOGFOOD CANDIDATE  
As of: 2026-08-19

## /goal

Preserve the existing X Article Engine capability while making it possible to render an article with a natural, author-neutral AI voice, then make the knowledge packet easy to attach to major AI providers through replaceable adapters.

The target is **not** to make a weaker generic writer. The target is to separate:

- capability that must survive;
- author/product preferences that should not be implicit defaults;
- provider-specific request shape;
- client/user content that must remain data rather than privileged instructions.

## Existing architecture discovered

The current public entry point uses `v09_final.build_generation_packet()` and `v09_final.audit_draft()`.

The engine already separates generation from publication and does not call an LLM itself. Its v0.9 chain contains substantial reusable capability:

- trusted evidence binding;
- primary/human attestation boundaries;
- invented-number and biography checks;
- commercial promise polarity checks;
- freshness and risk binding;
- secret/security guidance checks;
- terminology and comprehension guidance;
- anti-AI-boilerplate heuristics;
- long-form/mobile readability guidance;
- audience-depth and market-gap guidance;
- mandatory `/human` publication authority.

These are treated as capability, not as the developer's personal voice.

## Author/product defaults found during reverse engineering

The existing packet also contains preferences that should not become invisible defaults in a reusable Plain version.

Examples found in engine-owned policy text:

- a `reach_conversion_policy.goal_rule` that names `BridgePatch` as the default commercial destination;
- voice rules that intentionally preserve colloquial force/raw pain because the original engine was tuned against the developer's material;
- the human check `Would I actually say this?`, which assumes one known author;
- a final CTA example that names `無料適合確認`;
- historical examples/reference vocabulary containing product/tool names.

Plain v0 does **not** delete user-supplied occurrences of those names. If the brief itself is about BridgePatch, CapCut, or another named product, that remains article content. Plain removes only **engine-owned implicit defaults** from the provider-facing rule view.

## Surviving design

```text
verified brief
  -> existing v0.9 final packet
  -> Plain profile
     - capability unchanged
     - author imitation disabled
     - engine-owned product defaults neutralized
     - allowlisted provider-facing generation view
  -> provider adapter
     - constant system boundary
     - structured Plain view as user data
  -> model draft
  -> existing v0.9 audit
  -> mandatory /human
```

The existing v0.9 packet remains the capability source of truth. Plain is an additive overlay.

## Capability locks

Plainization fails closed if it changes these fields:

- `verified_source_refs`
- `verified_evidence`
- `verified_primary_info`
- `publication_state`
- `publication_authority`
- `external_publication_performed`
- `freshness`
- `risk_policy`
- `human_automation_boundary`
- `security_content_policy`
- `commercial_promise_polarity_policy`

It also requires:

```text
human_gate.required = true
publication_state = BLOCKED_PENDING_HUMAN
publication_authority = USER_ONLY
external_publication_performed = false
```

## Provider adapter discovery

No existing provider adapter layer was found inside `x_article_engine` during this pass, so the adapter boundary was reconstructed from the existing model-agnostic generation packet and current primary provider documentation.

Built-ins in Plain v0:

1. `openai_responses`
   - maps the constant engine boundary to Responses `instructions`;
   - maps the structured Plain payload to `input` user content;
   - emits `store: false` as the conservative adapter default.

2. `anthropic_messages`
   - maps the constant engine boundary to the top-level Messages `system` parameter;
   - maps the Plain payload to a user message.

3. `gemini_generate_content`
   - emits a REST-shaped `system_instruction` plus `contents` request;
   - leaves model-specific sampling values at provider defaults except for an explicit output-token ceiling.

Current primary references used for the mapping:

- OpenAI Responses / API documentation: https://platform.openai.com/docs/
- Anthropic Messages / Claude documentation: https://docs.anthropic.com/
- Gemini Generate Content documentation: https://ai.google.dev/api/generate-content

Provider schemas can change. The adapter is therefore a replaceable boundary, not engine truth.

## Adapter extension contract

`register_adapter(name, compiler)` provides explicit extension.

Deliberate constraints:

- no automatic plugin discovery;
- no automatic import of third-party adapters;
- built-in adapter names cannot be overwritten;
- a custom adapter receives only the allowlisted Plain generation view, not the raw engine packet;
- adapters compile request objects only and do not own API keys, credentials, HTTP clients, or publication authority.

This keeps "new provider support" cheap without giving an installed package silent prompt/credential authority.

## Prompt boundary

Dynamic article material is never interpolated into the built-in system instruction.

The provider system boundary is constant and states that:

- `payload.rules` are engine rules;
- `payload.content` and `payload.configuration` are data;
- instructions embedded inside offer/pain/evidence/primary information are not privileged;
- publication and human-review boundaries cannot be overridden by article content.

Unknown raw packet keys are omitted from the provider-facing view. A field such as `system_override` or `developer_prompt` therefore cannot become a new provider-level instruction merely by being added to a brief/packet.

## Credential boundary

Before any built-in or custom adapter receives the Plain view, the adapter layer scans for several common credential-like literal forms (for example long `sk-...`, GitHub token, Slack token, Google API key, and AWS access-key forms).

A suspected live literal blocks transmission and the exception does not echo the token. Redacted/example placeholders remain possible.

This is a conservative leak-prevention layer, not a complete secret scanner.

## What Plain v0 intentionally does not do

- call OpenAI, Anthropic, Gemini, or another provider;
- store API keys;
- auto-select a model;
- claim identical prose across providers;
- remove user-supplied brand names or attested opinions;
- weaken evidence, audit, risk, security, or `/human` gates;
- automatically imitate a client/person from their knowledge.

Client/person style overlays belong above Plain and require their own explicit profile/consent/evidence boundary.
