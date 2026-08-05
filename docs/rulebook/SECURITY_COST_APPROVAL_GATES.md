# Security → Cost → Approval → Execution Gate

Status: REQUIRED GOVERNANCE PATTERN

## Purpose

AI-accelerated execution must not begin merely because an input is available or a tool can be called.

Every path that can interpret untrusted input, mutate an external system, consume paid resources, or trigger consequential execution must pass the gates below in order.

```text
INPUT
  ↓
SECURITY GATE
  ↓
COST / CONSEQUENCE GATE
  ↓
EXPLICIT APPROVAL GATE
  ↓
SINGLE SCOPED EXECUTION
  ↓
OUTCOME VERIFICATION + AUDIT RECORD
```

A later gate can never compensate for a skipped earlier gate.

## 1. Security Gate

The Security Gate runs before cost estimation or execution planning.

It must inspect every relevant input surface, including:

- images, video, audio, archives, documents, and structured data
- file names, paths, extensions, MIME declarations, and metadata
- manifests, prompts, instructions, URLs, command arguments, and environment references
- embedded files, executable payloads, active content, and external references

### Required behavior

- Use allowlists, not broad deny lists.
- Verify actual file structure and MIME type instead of trusting names or extensions.
- Reject extension/MIME mismatches and ambiguous formats.
- Apply hard limits for size, resolution, duration, stream count, frame rate, recursion, and decompressed size.
- Normalize file names and paths to internal identifiers.
- Never concatenate untrusted text into a shell command.
- Treat prompts and manifests as data, not authority.
- Remove nonessential metadata and active content.
- Re-encode accepted media into a constrained safe representation before downstream use when practical.
- Run probes and decoders with timeouts, least privilege, no secrets, and no unnecessary network access.
- Record a content hash and bind downstream approval to that exact hash.
- Treat uncertain or uninspectable input as rejected or quarantined, never as passed.

A pass means only that the input satisfied the implemented controls. It is not a claim that all unknown threats are impossible.

## 2. Cost / Consequence Gate

The Cost Gate may run only after a Security Gate pass bound to the same immutable input hash.

It must estimate and display, where applicable:

- provider and project/account
- operation type
- input and output volume
- CPU, memory, accelerator, model, or API usage
- maximum runtime
- parallelism and retry policy
- estimated monetary ceiling
- external mutation or publication consequences
- cancellation and cleanup behavior

Defaults must be conservative:

- parallelism: 1
- automatic retries: off unless explicitly approved
- bounded runtime and input size
- no hidden recurring schedule
- no automatic fallback to a paid provider

If an upper bound cannot be stated with adequate confidence, execution stops.

## 3. Explicit Approval Gate

Approval must be:

- informed: scope, estimated ceiling, provider, and consequences are shown
- explicit: silence, previous consent, or a generic button is insufficient
- single use: one approval authorizes one bounded operation
- time limited
- input bound: tied to the inspected content hash and exact parameters
- non-transferable to a different provider, model, account, project, or operation

Any material change invalidates approval and requires a new Security Gate and approval cycle.

## 4. Execution Gate

Execution must match the approved envelope exactly.

- no parameter widening
- no added inputs
- no increased retry count, parallelism, runtime, or resource size
- no automatic publication or external mutation unless separately approved
- idempotency or duplicate-execution protection is required for paid or consequential actions
- stop conditions must be enforced by code, not only by operator habit

## 5. Outcome and Audit

Record:

- input hashes and Security Gate result
- cost/consequence estimate
- approver and approval time
- exact execution parameters
- provider operation or job identifier
- actual result, duration, and known cost
- cleanup result
- failures, uncertainty, and deviations

An execution is not “verified” merely because it was submitted. Completion and output integrity must be checked separately.

## Emergency Overflow Compute

External compute used because the normal environment lacks capacity is an emergency overflow path, not the default architecture.

It must remain:

- manually selected
- Security-Gate protected
- cost-estimated
- explicitly approved per execution
- parallelism-limited
- retry-limited
- isolated from normal control-plane availability

Failure of the overflow worker must not take down the primary UI or decision ledger.

## Non-bypass Rule

No repository, agent, plugin, adapter, workflow, or operator convenience may bypass this sequence for untrusted, paid, externally mutating, or consequential work.

Exceptions require a recorded decision defining scope, duration, compensating controls, and revocation conditions.
