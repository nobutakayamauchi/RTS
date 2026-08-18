# OSARU Concept Design → Ultimate Loop intake

Status: `CHALLENGER_KNOWLEDGE / NON_CANONICAL`

Sources:

- `おさる式コンセプトの極意` Google Slides.
- user-provided `コンセプトのエクセル.mp4`, provenance-bound in `concept-worksheet-video-supplement-20260818.json`.

## Coverage boundary

The public HTML presentation view exposed slide identities for `1..139`, but recoverable text only for `1..94`.

- `1..94`: text-recovered and mined.
- `95..139`: `UNKNOWN` (possibly image-only or otherwise inaccessible in the available view).

The worksheet video is a 70.033333-second, 512x1108, 30fps screen recording. Representative frames were extracted and visually inspected. No OCR-derived truth claim is used.

## Source structure recovered

The slide source repeatedly composes:

`demand -> actor-specific advantage -> competitive gap -> target/problem model -> downstream product/outcome -> one core concept -> adapter-specific rendering -> market feedback -> iteration`

The worksheet turns that concept into an explicit dataflow. Visible sections include:

`base strategy inputs -> launch-wide concept -> goal/phase/funnel selection -> prelaunch -> lead magnet -> Why/What/How/Action video structure -> landing page -> offer design`

A separate strategy column stores concrete upstream decisions, and later rows reuse earlier outputs as named inputs. This exposes dependency/staleness failure modes that the slide deck alone did not make as explicit.

## Surviving challenger deltas

### 1. Semantic-invariant adapter guard

`ONE SEMANTIC CORE != IDENTICAL PRESENTATION`

Protected semantics and provenance stay invariant, while presentation form may change. This refines the existing canonical-source support contract rather than creating a new subsystem.

### 2. Observation / inference layering

`OBSERVED SIGNAL != INFERRED LATENT NEED`

Raw observations, interpretations/hypotheses, and independently validated derived facts remain separately typed.

### 3. End-to-end objective binding

`LOCAL METRIC WIN != END-TO-END OUTCOME WIN`

This reinforces the existing frozen human-important outcome and same-workload comparison.

### 4. Context-conditioned telemetry

`AGGREGATE METRIC != UNIFORM EFFECT`

A material evidence-bound cohort/context may invalidate a global diagnosis. Arbitrary or immaterial post-hoc segmentation cannot veto the aggregate.

### 5. Derived-artifact staleness propagation

The worksheet visibly threads earlier decisions into later assets. Generalized:

`UPSTREAM DECISION CHANGE => DEPENDENT DERIVED ARTIFACT STALE UNTIL RECOMPUTED OR REVALIDATED`

This is field-sensitive, not a demand to rebuild everything. If the changed upstream field is outside a derived artifact's declared dependency set, the artifact stays current. If an affected field changed, the artifact is stale until recomputed from the current upstream revision or boundedly revalidated.

This survives as a strong canonical evidence/control candidate.

### 6. Context-bound policy selection

The worksheet explicitly asks for business phase before selecting a funnel/policy. Generalized:

`CONTEXTUAL POLICY != UNIVERSAL POLICY`

A policy selected for a material maturity/risk/operating context cannot silently become universal doctrine. If the context that selected it changes, the policy is stale until re-evaluated.

This currently looks more like a profile/selection refinement than a wholly new subsystem.

### 7. Abstraction-level binding

The worksheet includes an explicit concept abstraction-level check. Generalized:

`ABSTRACT SUCCESS != REFUTATION OF CONCRETE FAILURE`

and

`NARROW EVIDENCE != BROADER CLAIM WITHOUT SCOPE BRIDGE`

A broad statement such as “the system works” cannot erase a concrete checkout failure, while one passing component cannot establish whole-system correctness without validated coverage. This overlaps construct-validity/context guards but adds a useful anti-evasion scope check.

## Support-only / deliberately rejected as universal doctrine

- specific social-platform preferences;
- fixed concept/copy formulas;
- Why/What/How/Action as mandatory for all workloads;
- fixed launch/funnel patterns;
- fixed high-ticket product assumptions;
- story/authority as proof of factual correctness;
- inferred latent needs treated as observed customer facts;
- persuasive claims that a prior solution is causally wrong without independent evidence;
- universal targeting, funnel, or messaging rules.

## Hard invariants retained

`PERSUASIVE NARRATIVE != CAUSAL EVIDENCE`

`OBSERVATION != INTERPRETATION`

`AGGREGATE != UNIFORM`

`LOCAL OPTIMUM != PROTECTED OUTCOME`

`UPSTREAM CHANGE != DOWNSTREAM FRESHNESS`

`CONTEXTUAL POLICY != UNIVERSAL POLICY`

`ABSTRACT SUCCESS != REFUTATION OF CONCRETE FAILURE`

`CONTRACT METEOR PASS != CANONICAL PROMOTION`
