# Ultimate Loop — New-Build Architecture Superiority Gate

Date: **2026-08-14**

Status: `CANONICAL_EXTENSION_CANDIDATE`

## Rule

Reuse-first remains the default, but the existence of an external service or incumbent implementation does not permanently prohibit new construction.

There are two valid paths to a bounded new-build candidate:

1. **Irreducible responsibility** — no existing holder, composition, bounded manual process, or extracted glue can safely carry the surviving responsibility.
2. **Architecture superiority** — existing services or implementations exist, but their architecture is materially weak for the frozen workload and a bounded new design can demonstrate materially better whole-life fitness under the same comparison standard.

## Architecture-superiority path

`INCUMBENT EXISTS + MATERIAL ARCHITECTURE DEFICIT -> BOUNDED CHALLENGER -> SAME FROZEN WORKLOAD -> METEOR -> PROVEN SUPERIORITY -> PROMOTION ELIGIBLE`

A material architecture deficit may include quality/capability limits, throughput or latency ceilings, poor resource efficiency, reliability problems, high operator burden, security/privacy weakness, maintainability burden, excessive whole-life cost, dependency/provider risk, weak recovery or rollback, or disproportionate complexity.

A benchmark result alone is not sufficient. Comparison must include the relevant whole-life dimensions: quality/capability, performance/efficiency, reliability, operator burden, security/privacy, maintainability, cost, migration/rollback, dependency risk, recoverability/PHOENIX implications, evidence maturity, and explicit promotion authority.

A candidate cannot claim superiority by omitting inherited safety, durability, authority, recovery, or evidence requirements.

## Prototype versus promotion

Evidence of a material architecture deficit can justify a bounded prototype. It does not authorize promotion.

`PROTOTYPE AUTHORIZED != PROMOTION AUTHORIZED`

## Canonical extension

> **Reuse first, but do not preserve an inferior architecture merely because it already exists.**

Operationally:

`KEEP EXISTING -> EXTRACT / COMPOSE -> IRREDUCIBLE GAP OR MATERIAL ARCHITECTURE DEFICIT -> BOUNDED NEW BUILD CANDIDATE -> METEOR -> KEEP / PARTIAL / REPLACE / RETIRE`
