# BridgePatch Sales Campaign Manifest — 2026-08-15

Status: `HUMAN_GATE_PASSED / PRIVATE_HANDOFF_GENERATED / READY_FOR_USER_PLATFORM_ACTION`

Source:

`post_adapter/campaigns/bridgepatch-sales-20260815/source.json`

Current Post Adapter / Publication Bridge state:

```text
CHANNEL_POLICY: x
CONTENT_BUDGET: 260 unicode codepoints per body
FACT_PRIORITY: enabled
OVERFLOW_STRATEGY: thread
verified facts: 5
verification warnings: 0
/human: PASSED
/human evidence preservation: PASSED
X post blocks after /human: 2
X body sizes after /human: 163 / 193 unicode codepoints
Publication Bridge state: APPROVED_FOR_HANDOFF
publication authority: USER_ONLY
automatic publication: false
credential storage: false
private API usage: false
external publication performed by tooling: false
```

Final external-facing drafts:

- `x.md` — `/human` reviewed
- `note.md` — `/human` reviewed
- `github.md` — retained technical/discovery copy

The exact X/note drafts are SHA-256 bound by the `/human` handoff record. Any edit after `/human` requires the gate to be run again before Publication Bridge may hand the content to a platform.

The actual composer/editor handoff UI is intentionally **not committed to this public repository**. A public-repo handoff page would expose the unpublished draft before the user performs the final platform action. The handoff is generated privately for the current launch session instead.

Discovery targets:

- Sales page: `https://nobutakayamauchi.github.io/RTS/bridgepatch/`
- GitHub Pages home: BridgePatch discovery card live
- Repository README: BridgePatch current-service route live
- Gmail: `yamauchi.rts.office@gmail.com`

Post-publication observation uses:

`bridgepatch/LAUNCH_OBSERVATION.md`

Minimal funnel:

```text
SEEN -> VISIT -> INQUIRY -> FIT_CHECK -> PAID_SPEC
```

Operating boundary:

- final X/note publish action remains human/user controlled;
- no automatic X post;
- no automatic note post;
- no mass DM/outreach;
- no new large-product development;
- no unsupported customer/revenue claims;
- `QUALIFIED INBOUND > NEW FEATURE WORK`.
