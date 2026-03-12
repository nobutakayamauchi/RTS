# RTS Example Run

Run ID: RUN_EXAMPLE_001

Purpose

This example demonstrates how RTS records a real decision process during AI-assisted execution.

The example is simplified but reflects the intended structure of an RTS run record.


---

SPAN 001

Context

Repository documentation structure is becoming difficult to navigate.
Multiple documents exist but their roles are unclear.

Decision

Introduce RTS_EXAMPLES.md to provide concrete usage examples of the protocol.

Constraints

The repository must remain readable for both operators and external readers.

Assumptions

Concrete examples will improve understanding of the protocol and reduce ambiguity.

Action

Create RTS_EXAMPLES.md and populate it with decision reconstruction scenarios.

Outcome

The documentation structure now includes a practical demonstration layer.


---

SPAN 002

Context

RTS documentation now includes protocol definition and specification.

Decision

Add a minimal operational run example to demonstrate how RTS records execution history.

Constraints

The example must remain simple and readable.

Assumptions

A minimal example run will help developers understand how RTS logs operate.

Action

Create runs/example_run.md as a reference run record.

Outcome

RTS repository now contains a complete documentation stack:

Protocol definition  
Specification  
Operational examples  
Execution run record


---

SPAN 003

Context

AI-assisted development environments accelerate execution beyond manual tracking.

Decision

Use append-only structured run records to preserve decision history.

Constraints

The system must remain compatible with Git-based workflows.

Assumptions

Git commit history provides reliable timestamps and version integrity.

Action

Adopt Git-native run logging structure under runs/.

Outcome

Decision history becomes reconstructable through structured run records.


---

End of Run

This example demonstrates how RTS records decision snapshots and execution transitions.

The goal is not to judge decisions but to preserve the structure that allows them to be reconstructed later.
