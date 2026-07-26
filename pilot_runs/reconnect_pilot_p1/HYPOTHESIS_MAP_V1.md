# Hypothesis Map v1

## Confirmed decisions

- P1 precedes P3 implementation.
- P3 uses one fixed public RTS evidence boundary.
- WIP remains 1.
- Human review controls consequential decisions.
- Public, provider, contract, and external actions remain unauthorized.

## Testable product hypotheses

| ID | Hypothesis | Test | Falsification signal |
|---|---|---|---|
| H1 | Repository history contains useful achievements the subject has not explicitly described | Generate 10 candidates from the fixed RTS range | Fewer than 3 genuinely overlooked candidates survive review |
| H2 | Exact evidence links reduce exaggeration | Review candidate claims against source artifacts | Reviewers cannot tell why a claim is supported |
| H3 | Human/AI contribution can be represented without pretending perfect attribution | Produce contribution maps with uncertainty | Most candidates collapse into unsupported attribution |
| H4 | One canonical record can produce several audience-specific drafts | Produce technical, customer, and collaboration phrasing | Outputs require independent manual reconstruction |
| H5 | The output can become a paid manual report | Create a sample deliverable and later test interest | Target users do not understand or value the deliverable |

## Unknowns

First buyer, price, sales channel, report length, preferred public format, acceptable human-review time, external repository diversity, and legal obligations for customer-submitted data.

## Guardrail hypotheses

- False positives will occur and must be rejectable.
- Contribution ambiguity must be represented, not hidden.
- One CASE cannot validate platform-level claims.
