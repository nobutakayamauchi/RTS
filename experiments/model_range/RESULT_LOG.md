# RTS Model Range Result Log

## Benchmark target
- Repository: `nobutakayamauchi/RTS`
- Branch: `experiment/model-range-rts-001`
- Prompt: `experiments/model_range/PROMPT_01_REPO_RECON.md`
- Mode: whole-repository reconnaissance, read-only
- Purpose: measure cost/quality scaling on a materially larger real repository and compare models using the same target and prompt.

## Baseline from prior small benchmark
- Small target: RIGHT ARM Capability Economy bounded audit
- GPT-6 Astra / Low / Fast OFF: observed cost `$0.66`
- GPT-5.6 Sol: observed discounted cost about `$0.14`; user-normalized non-discount estimate about `$0.24`
- Initial normalized Astra/Sol ratio: about `2.75x`
- This ratio is only a prior; do not assume it stays linear as target size grows.

## SHOT-RTS-SOL-01
- Model: GPT-5.6 Sol
- Thinking:
- Fast mode:
- Discount shown:
- Credit before: `$4.20` (latest observed balance before this benchmark; verify immediately before firing)
- Credit after:
- Observed discounted consumption:
- Normalized non-discount consumption:
- Start time:
- End time:
- Elapsed:
- Files/areas inspected:
- Finding count:
- Final recommendation:
- Scope discipline notes:
- Repository-specific evidence quality:
- Important structural insights:

### Gate after Sol reconnaissance
- [ ] STOP — Sol reconnaissance itself is too expensive; split target before any Astra shot.
- [ ] TARGETED_ASTRA — Sol found bounded high-value deep-dive targets; fire Astra only at those.
- [ ] WHOLE_REPO_ASTRA — Sol cost is low enough and coverage good enough to justify a same-prompt whole-repo Astra comparison.

## SHOT-RTS-ASTRA-01
- Only run after the Sol gate above.
- Model: GPT-6 Astra
- Thinking:
- Fast mode:
- Credit before:
- Credit after:
- Consumption:
- Elapsed:
- Files/areas inspected:
- Finding count:
- Final recommendation:
- Unique findings versus Sol:
- Findings shared with Sol:
- Findings where Sol and Astra disagree:
- Astra-only value that can be externalized into reusable rules/maps/checklists:

## Comparison
- Observed cost ratio Astra/Sol:
- Normalized cost ratio Astra/Sol:
- Quality gap:
- Scope-efficiency gap:
- Unique architectural insight gap:
- Can Astra's advantage be transferred into Sol/Codex procedures?:
- Recommended routing policy update:
