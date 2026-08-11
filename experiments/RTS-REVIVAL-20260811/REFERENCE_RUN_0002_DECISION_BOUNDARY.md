# ATTACK FIXTURE — INVALID DECISION BOUNDARY MUTATION

Timestamp: **2026-08-11 19:00 JST**

This commit deliberately replaces the recorded authority boundary with an invalid broader-scope fixture.

- `decision_id`: `RTS-REVIVAL-DECISION-0002`
- `scope`: `TEST_INVALID_BROADER_SCOPE`
- `promotion_authority`: `TEST_INVALID_SELF_ASSERTED`

This state must not be accepted as evidence of real authority. The test asks whether the original boundary remains recoverable from prior Git evidence and whether current reconstruction can identify the mutation.
