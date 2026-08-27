# Official Docs Intake + Claim Extraction Adapter v1

I is the upstream documentation intake adapter for H (`model_transition_intelligence`).

```text
provider + generation + query terms
        ↓
bounded official index/seed discovery
        ↓
HTTPS fetch + redirect host revalidation
        ↓
immutable raw digest + visible-text normalization
        ↓
exact-anchor conservative claim extraction
        ↓
coverage audit
        ↓
transition-evidence-bundle/v1
        ↓
H → F → G
```

## Hard boundary

`FETCHED DOC != OBSERVED MODEL BEHAVIOR`

`EXTRACTED CLAIM != VERIFIED BEHAVIOR`

I never claims hidden neural architecture and never grants execution, profile-application, or promotion authority.

## Provider trust

Built-in v1 policies cover OpenAI, Anthropic and Google. A source is `OFFICIAL` only when its final HTTPS host is allowlisted by the selected provider policy. Page content cannot self-promote an arbitrary host to official trust.

Redirects are revalidated before following. The adapter has no credential interface and no arbitrary-host escape hatch.

## Discovery

Discovery is bounded, not a general crawler. It reads a small configured set of provider documentation indexes/seeds, scores links against the requested generation/product terms, deduplicates them and returns at most eight document URLs.

Current provider roots include:

- OpenAI developer/API documentation indexes and model guidance;
- Anthropic/Claude Platform `llms.txt`, models overview and migration guide;
- Google Gemini API model documentation.

## Fetch and normalization

- HTTPS only.
- Exact provider-host allowlist.
- Redirect final host revalidated.
- Max eight product documents per intake.
- Max 2 MB raw body per document.
- Max 240k normalized characters per document, below H's source limit.
- HTML is parsed as inert text; `script`, `style`, `noscript`, `svg`, `canvas`, navigation/header/footer/aside content is ignored.
- No JavaScript is executed.

Raw SHA-256 and normalized-content SHA-256 are preserved separately.

## Claim extraction

The built-in extractor is intentionally conservative and deterministic. It identifies explicit exact-text anchors for contract areas already understood by H, including context, reasoning/thinking, tools, caching, delegation, sandbox, response schema, streaming, state, instructions, errors/retries, auth/permissions, pricing/performance, identity, limits and deprecations.

Each claim:

- copies its `anchor` exactly from normalized source text;
- remains `behavior_status=UNVERIFIED`;
- carries no runtime authority;
- is validated by H before the bundle is returned.

This v1 does not call a model to paraphrase or semantically invent claims.

## Coverage audit

A contract-like text block that triggers the generic contract signal but matches no extraction rule is not silently discarded. It appears in `audit.documents[].extraction.ambiguous` and the report becomes `REVIEW_REQUIRED`.

Similarly, a failed product-document fetch prevents `READY_FOR_H`. Successfully fetched documents remain in the partial bundle for review; completed evidence is not erased by a later failure.

`READY_FOR_H` therefore means:

1. an H-valid bundle exists;
2. selected product-document fetches all succeeded;
3. no contract-like block remained ambiguous.

Provider index discovery failures are recorded separately because explicit/seed product documents may still form a complete usable bundle.

## CLI

```bash
python -m official_docs_intake policy openai
python -m official_docs_intake discover --provider openai --term gpt-5.6 --max-documents 5
python -m official_docs_intake build --request request.json --output report.json
python -m official_docs_intake verify --report report.json
```

A request contains `provider`, `product_surface`, `generation`, `captured_at`, optional `query_terms`, optional explicit official URLs, max document count, and optional stable `document_id`/`source_type` overrides.

## What v1 deliberately does not do

- unrestricted internet crawling;
- authenticated/private documentation access;
- browser or JavaScript execution;
- model/API based semantic extraction;
- hidden architecture inference;
- automatic H/F/G execution;
- automatic profile mutation or Canon promotion.
