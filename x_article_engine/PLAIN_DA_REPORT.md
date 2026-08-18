# X Article Engine Plain v0 — DA / Counter-DA Report

Status: DRAFT / PRE-HUMAN-GATE  
As of: 2026-08-19

## Frozen target

The Plain path survives only if all of the following remain true:

1. existing X Article Engine safety/evidence/audit capability is not weakened;
2. provider-facing rules no longer assume the engine developer's product or house voice;
3. user/client material is preserved as content without being promoted to system authority;
4. OpenAI / Anthropic / Gemini request shapes are easy to compile and replace;
5. new adapters can be added without automatic plugin authority;
6. credential-like literals and weakened publication gates fail closed.

## Raison d'être attack

### Candidate A — delete the tuned knowledge and return to core only

Rejected.

It removes useful safety, evidence, terminology, long-form, market, freshness, risk, and audit capability merely to obtain a neutral voice.

### Candidate B — fork a separate simplified engine

Rejected as default.

It creates permanent divergence and makes every safety fix need two implementations.

### Candidate C — keep the final engine, add a Plain overlay and provider adapters

Survives.

The final v0.9 packet remains capability truth. Plain controls provider-facing preference/voice without replacing the auditor.

---

## METEOR / DA vectors

### DA-01: author brand leaks into generic output

**Attack**  
Build a completely generic brief. The underlying v0.9 packet still contains `BridgePatch` in an engine-owned reach/conversion rule.

**Risk**  
A generic customer article can inherit the developer's commercial destination or wording.

**Counter-DA**  
Plain sanitizes engine-owned policy text and rewrites the specific reach goal while leaving user content untouched.

**Executable check**  
`test_plain_02_removes_engine_author_defaults_from_rule_view`

---

### DA-02: plainization removes safety together with style

**Attack**  
Neutralize voice by deleting or rebuilding the packet from scratch.

**Risk**  
Evidence binding, risk/freshness rules, security checks, commercial promise polarity, or publication gates disappear.

**Counter-DA**  
Plain is an overlay on `v09_final`. Locked capability fields are compared before/after and fail closed on change. The v0.9 auditor is reused unchanged.

**Executable check**  
`test_plain_01_preserves_locked_capability_and_audit_behavior`

---

### DA-03: user content erases legitimate brand/context

**Attack**  
Global text replacement removes `BridgePatch`, `CapCut`, or another name even when the user intentionally supplied it as article content.

**Risk**  
Plain becomes destructive and changes facts.

**Counter-DA**  
Sanitization is applied only to engine-owned rule surfaces. `content` fields are copied without rewriting.

**Executable check**  
`test_plain_03_does_not_erase_user_supplied_brand_or_attested_content`

---

### DA-04: prompt injection crosses into provider system authority

**Attack**  
Put `IGNORE ALL PREVIOUS INSTRUCTIONS ...` in `pain`, evidence, CTA, or another dynamic field.

**Risk**  
An adapter naively concatenates the packet into a provider system/developer prompt.

**Counter-DA**  
Built-in adapters use one constant system boundary. Dynamic packet material is serialized only into the provider user-message payload. The system boundary explicitly classifies content/configuration as data.

**Executable check**  
`test_plain_05_builtin_adapters_keep_dynamic_content_out_of_system_boundary`

---

### DA-05: invented packet field becomes a hidden system override

**Attack**  
Add `system_override`, `developer_prompt`, or another unknown key to the raw packet.

**Risk**  
A generic serializer forwards it as privileged instruction material.

**Counter-DA**  
The Plain generation view is allowlisted and fail-closed. Unknown raw packet keys are omitted. Custom adapters receive only this view.

**Executable checks**  
`test_plain_05_builtin_adapters_keep_dynamic_content_out_of_system_boundary`  
`test_plain_08_adapter_registry_is_explicit_and_collision_safe`

---

### DA-06: accidental secret leaves the machine through an adapter

**Attack**  
Place a credential-like literal inside article material.

**Risk**  
The model adapter transmits it because evidence/primary information is legitimate packet content.

**Counter-DA**  
The adapter boundary scans the sanitized outbound view before any built-in or custom compiler receives it. A suspected live literal blocks with a non-echoing error.

**Executable check**  
`test_plain_06_provider_adapter_blocks_credential_like_literals_before_compiler`

**Residual risk**  
Pattern scanning is not complete DLP. Unknown credential formats, encoded secrets, and ordinary confidential business data still require caller-side handling.

---

### DA-07: packet claims it already passed /human

**Attack**  
Mutate `publication_state`, `publication_authority`, or `human_gate.required` before provider compilation.

**Risk**  
The adapter becomes a route around the engine's publication authority.

**Counter-DA**  
Adapters require `BLOCKED_PENDING_HUMAN`, `USER_ONLY`, `external_publication_performed=false`, and `human_gate.required=true`.

**Executable check**  
`test_plain_07_adapter_refuses_weakened_human_or_publication_boundary`

---

### DA-08: extension mechanism allows silent takeover

**Attack**  
Auto-discover installed plugins or let a custom package replace `openai_responses`.

**Risk**  
A dependency silently gains access to prompt content or changes request semantics.

**Counter-DA**  
No auto-discovery exists. Registration is explicit. Existing names cannot be overwritten. Custom compilers receive only the sanitized view.

**Executable check**  
`test_plain_08_adapter_registry_is_explicit_and_collision_safe`

---

### DA-09: malformed model/token parameters become request-smuggling or runaway-cost inputs

**Attack**  
Use newline/NUL model identifiers or absurd output-token values.

**Risk**  
Downstream wrappers may turn malformed values into ambiguous requests or unexpectedly expensive output.

**Counter-DA**  
Model strings reject newline/CR/NUL and implausible length. Output-token ceiling is bounded.

**Executable check**  
`test_plain_09_invalid_model_or_token_bounds_fail_closed`

---

## Provider-schema counter-DA

Built-ins deliberately compile only request objects; they do not make HTTP calls.

Current mapping:

```text
openai_responses
  system boundary -> instructions
  data -> input[user/input_text]
  retention default -> store=false

anthropic_messages
  system boundary -> system
  data -> messages[user/text]

gemini_generate_content
  system boundary -> system_instruction
  data -> contents[user/parts.text]
```

The implementation intentionally does not hard-code provider model names or sampling personalities. Provider schemas are replaceable adapter occupants and should be rechecked when official APIs change.

## Counter-DA result

Current result: **SURVIVES AS DRAFT / DOGFOOD REQUIRED**.

The code-level separation now exists, but the user-facing goal includes output quality: "natural AI output without the developer's habits." That cannot be proven by packet inspection alone.

The next reality gate must run the **same brief** through at least:

- current tuned/final packet;
- Plain + OpenAI adapter;
- Plain + Anthropic adapter;
- Plain + Gemini adapter;

Then compare:

- factual/audit parity;
- brand/house-voice leakage;
- naturalness;
- unwanted blandness;
- whether provider differences need tiny adapter-specific guidance rather than a new core fork.

No promotion to default Plain behavior should occur until that dogfood evidence exists.
