# PROMPT 01 — RTS Whole-Repository Reconnaissance Benchmark

You are conducting a bounded, read-only architectural reconnaissance benchmark on this repository snapshot.

## Objective
Treat the entire repository as the target and determine its current system topology, major structural risks, and highest-value deep-dive targets.

This is NOT a line-by-line exhaustive review. Start from the repository tree, identify the important subsystems, and inspect only the files needed to support evidence-based conclusions. Optimize for architectural information gained per file read.

## Rules
- READ ONLY.
- Do not edit, create, delete, commit, open a PR, merge, deploy, or change settings.
- Do not use external web sources.
- Do not inspect git history unless absolutely necessary to resolve a current-state contradiction.
- Do not run long builds or broad test suites.
- Do not redesign unrelated product behavior.
- Do not assume README/docs are authoritative; cross-check claims against implementation/config/tests/workflows where relevant.
- Separate observed fact from inference.
- Every structural finding must name the exact repository paths that support it.
- If the repository is too large to inspect deeply within a reasonable pass, do not silently pretend coverage is complete. Report coverage and uncertainty explicitly.
- Maximum 8 findings.
- Keep the final answer concise; avoid tutorial material and generic software advice.

## What to determine
1. What are the major subsystems and how do they relate?
2. Which parts appear to be active core, experimental, legacy, duplicated, superseded, or disconnected?
3. Where do documentation, code, tests, workflows, and runtime assumptions contradict each other?
4. What are the 3 highest-value areas for a deeper second-pass audit?
5. Is the current repository better handled as one system, or should it be split into bounded audit domains before further work?

## Required output
### A. Coverage
- Approximate repository areas/directories inspected.
- Number of files inspected if you can determine it.
- Important areas intentionally not inspected or only sampled.

### B. System map
- Up to 10 major components/subsystems.
- One sentence each describing role and major dependency/relationship.

### C. Structural findings
For each finding, provide:
- Severity: Critical / High / Medium
- Observed fact
- Risk or consequence
- Exact supporting paths
- Minimal next action

Maximum 8 findings.

### D. Deep-dive targets
Rank the top 3 next audit targets and explain why each has the highest expected information value.

### E. Work split
State what can safely be delegated to a cheaper implementation/review model and what, if anything, genuinely requires a scarcer high-reasoning model.

### F. Final recommendation
Choose exactly one:
- `WHOLE_REPO_OK`
- `SPLIT_BEFORE_DEEP_AUDIT`
- `TARGETED_REPAIR_FIRST`
- `INSUFFICIENT_COVERAGE`

Finally list the exact files inspected. If the list is very large, group by directory and provide counts plus the most important paths.
