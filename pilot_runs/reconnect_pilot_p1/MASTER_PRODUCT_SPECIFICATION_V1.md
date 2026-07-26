# Master Product Specification v1

## 1. Identity

- Working product name: **Proof Engine**
- Umbrella concept: **Reconnect**
- Product state: internal specification, not public launch
- Current approved path: P1 specification, then a separately gated P3 minimum vertical slice

## 2. Purpose

Proof Engine discovers overlooked work value from exact evidence, separates fact from interpretation, maps human/AI/collaborator contribution, translates approved value for a defined audience, and prepares reusable assets without automatically publishing or acting on them.

The wider Reconnect concept may later connect approved value to work, customers, collaborators, opportunities, or support and observe what changed. Those branches are not part of the first implementation.

## 3. Core problem

Useful work exists in repositories, PRs, issues, specifications, tests, and development logs, but it is often fragmented across artifacts, invisible to its creator, described as activity rather than value, stripped of the human decisions behind AI-assisted output, difficult for outsiders to understand, or exaggerated when translated without evidence discipline.

## 4. First audience and buyer hypothesis

### First user

AI-assisted solo developers and solo founders with public GitHub history and weak external value translation.

### First buyer hypothesis

The same individual, a collaborator, a small business owner, or a hiring/partnering party who needs an evidence-backed explanation of what was actually accomplished.

### First paid-product hypothesis

Evidence-Backed Achievement Discovery Report. The report converts one fixed repository or PR set into approved achievement claims, contribution maps, evidence strength, and reusable portfolio or sales copy.

## 5. Product stages

1. Source registration
2. Activity extraction
3. Achievement candidate generation
4. Evidence linking
5. Contribution mapping
6. Value translation
7. Human decision
8. Output-asset drafting
9. Optional later market-signal observation

P3 implements stages 1 through 8 only.

## 6. Actors

- Subject: person or project whose work is analyzed
- Operator: runs the bounded process
- Reviewer: approves, revises, rejects, redacts, or expires claims
- Evidence source: exact repository/PR/spec/test/log objects
- Audience: intended reader of an approved output
- AI/tool: assists extraction or translation but has no approval authority

## 7. Product modules

### P3 modules

- Fixed Source Loader
- Activity Extractor
- Candidate Builder
- Evidence Linker
- Contribution Mapper
- Value Translator
- Human Review Queue
- Output Draft Builder
- Deterministic Manifest and Checkpoint

### Frozen modules

- automatic publishing or outreach
- customer-data ingestion
- opportunity matching
- Support Fit automation
- human ranking
- Talent DB / DNS Wave
- provider orchestration
- autonomous multi-repository crawling

## 8. Operating lanes

- Product implementation: WIP=1
- Public evidence: separate human gate
- Immediate cash validation: manual only
- Grants/funding: separate research lane
- Legal/privacy: required before external customer data

## 9. Evidence policy

Every claim has one evidence label: VERIFIED, INFERRED, SELF_REPORTED, UNVERIFIED, or CONFLICTED.

VERIFIED requires exact committed or independently reproducible evidence. AI-generated explanations are never VERIFIED solely because they are plausible.

## 10. Human authority

Only a human may approve, revise, reject, redact, expire, publish, contact, contract, accept support, widen scope, or authorize provider/repository actions.

## 11. Privacy

P3 accepts public RTS repository evidence only. Credentials, private repositories, health, family, employment disputes, legal matters, financial details, location, and third-party personal data are excluded.

## 12. Determinism and reconstruction

A run fixes source references, source fingerprints, configuration, generated candidates, evidence links, human decisions, output drafts, and checkpoint. The same accepted inputs must reproduce the same pre-review candidate set.

## 13. Failure handling

Fail closed for missing evidence, source drift, manifest mismatch, duplicate IDs, path escape, unknown labels, unapproved public text, authority widening, or repeated failed action without new evidence.

## 14. Success definition for P3

- one fixed RTS source boundary;
- at least 10 candidates;
- every candidate has evidence links and a label;
- human/AI/collaborator contribution can be represented;
- inflated claims can be rejected;
- one approved output-asset draft can be generated;
- no publication or external action occurs.

## 15. Non-goals

No global ranking, hiring decision, support-recipient selection, outcome guarantee, automatic sales, platform build, multi-case proof, or general claim that this system reconnects people successfully.
