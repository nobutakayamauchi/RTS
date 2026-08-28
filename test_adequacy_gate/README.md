# False-Green Test Adequacy Gate v1

K2 validates the **ability of the K1 test surface to detect faults**. It does not claim that green tests prove bug absence.

Mandatory lanes:

- known-bad injection;
- critical mutation testing;
- held-out cases;
- metamorphic properties;
- mutation-harness controls.

Mutation rules are fail-closed:

- a critical mutant must match the source exactly once;
- it must import successfully before it can be counted as a behavioral kill;
- syntax/import failure is `INVALID_MUTANT`, not `KILLED`;
- an equivalent/no-op control must survive;
- mutation execution happens in a temporary package copy and the production K1 source hash must remain unchanged.

`ADEQUATE` requires every mandatory lane to pass. A high mutation-kill percentage cannot mask a failed held-out, known-bad, metamorphic, or harness-control lane.

K2 has no semantic truth, execution, profile-application, promotion, Canon, or evidence-drop authority.
