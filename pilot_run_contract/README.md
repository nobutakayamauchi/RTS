# Governed Pilot Seed / Run Contract v1

This package validates the exact seed used to load the first real-world project into the loop engine.

The committed CASE-001 seed fixes:

- final and current goals
- completion and stop conditions
- WIP=1
- checkpoint and resume policy
- required evidence-backed outputs
- explicit human gates
- a non-authorizing execution boundary

Commands:

```text
python -m pilot_run_contract.cli verify
python -m pilot_run_contract.cli summary
```

The package has no execute, apply, publish, provider, commit, merge, or repository-write command. It proves only that the test project is shaped well enough to enter a governed pilot run.
