from __future__ import annotations

import copy
import importlib.util
import pathlib
import unittest


MODULE_PATH = pathlib.Path(__file__).with_name("task_envelope.py")
spec = importlib.util.spec_from_file_location("reconstruction_furnace_task_envelope", MODULE_PATH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TaskEnvelopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = {
            "repo": "alien/example",
            "pull_number": "999",
            "instance_id": "alien__example-999",
            "issue_numbers": ["123"],
            "base_commit": "a" * 40,
            "patch": "SECRET GOLD PATCH",
            "test_patch": "SECRET GOLD TEST",
            "problem_statement": "Observed behavior differs from the documented contract.",
            "hints_text": "SECRET HINT",
            "all_hints_text": "SECRET ALL HINTS",
            "commit_urls": ["https://example.invalid/fix"],
            "commit_url": "https://example.invalid/base",
            "rebuild_cmds": ["make -j2"],
            "test_cmds": ["make check"],
            "print_cmds": ["cat test-output.log"],
            "log_parser": "SECRET EVALUATOR PARSER",
            "FAIL_TO_PASS": ["hidden_failure"],
            "PASS_TO_PASS": ["hidden_regression"],
            "docker_image": "example.invalid/furnace:task",
            "future_dataset_field": {"may_contain": "anything"},
        }

    def test_allowlist_drops_all_answer_bearing_source_fields(self) -> None:
        envelope = mod.sanitize_for_solver(
            self.source,
            opaque_task_id="FURNACE-A-001",
            task_valid=True,
        )
        self.assertEqual(set(envelope), mod.ENVELOPE_KEYS)
        self.assertEqual(mod.forbidden_key_scan(envelope), [])
        serialized = repr(envelope)
        self.assertNotIn("SECRET GOLD PATCH", serialized)
        self.assertNotIn("SECRET GOLD TEST", serialized)
        self.assertNotIn("SECRET HINT", serialized)
        self.assertNotIn("hidden_failure", serialized)
        self.assertNotIn("future_dataset_field", serialized)
        self.assertNotIn("alien__example-999", serialized)
        self.assertNotIn("999", serialized)

    def test_unknown_solver_field_fails_closed(self) -> None:
        envelope = mod.sanitize_for_solver(
            self.source,
            opaque_task_id="FURNACE-A-002",
            task_valid=True,
        )
        envelope["innocent_future_field"] = "value"
        with self.assertRaises(mod.TaskEnvelopeError):
            mod.verify_solver_envelope(envelope)

    def test_forbidden_field_fails_closed_even_if_empty(self) -> None:
        envelope = mod.sanitize_for_solver(
            self.source,
            opaque_task_id="FURNACE-A-003",
            task_valid=True,
        )
        envelope["patch"] = ""
        with self.assertRaises(mod.TaskEnvelopeError):
            mod.verify_solver_envelope(envelope)
        self.assertEqual(mod.forbidden_key_scan(envelope), ["patch"])

    def test_invalid_task_never_enters_solver(self) -> None:
        with self.assertRaises(mod.TaskEnvelopeError):
            mod.sanitize_for_solver(
                self.source,
                opaque_task_id="FURNACE-A-004",
                task_valid=False,
            )

    def test_validator_requires_exactly_three_gold_runs(self) -> None:
        with self.assertRaises(mod.TaskEnvelopeError):
            mod.build_validator_provenance(
                self.source,
                gold_validation_runs=2,
                gold_validation_passes=2,
            )

        provenance = mod.build_validator_provenance(
            self.source,
            gold_validation_runs=3,
            gold_validation_passes=3,
        )
        self.assertTrue(provenance.task_valid)
        self.assertNotIn("alien__example-999", repr(provenance))
        self.assertNotIn("SECRET GOLD PATCH", repr(provenance))

    def test_three_runs_with_one_failure_is_not_valid(self) -> None:
        provenance = mod.build_validator_provenance(
            self.source,
            gold_validation_runs=3,
            gold_validation_passes=2,
        )
        self.assertFalse(provenance.task_valid)

    def test_recursive_scan_detects_trace_leakage(self) -> None:
        trace_namespace = {
            "events": [
                {"type": "TASK_START"},
                {"type": "TOOL_RESULT", "payload": {"test_patch": "oops"}},
            ]
        }
        self.assertEqual(mod.forbidden_key_scan(trace_namespace), ["test_patch"])

    def test_source_is_not_mutated(self) -> None:
        before = copy.deepcopy(self.source)
        mod.sanitize_for_solver(
            self.source,
            opaque_task_id="FURNACE-A-005",
            task_valid=True,
        )
        self.assertEqual(self.source, before)


if __name__ == "__main__":
    unittest.main()
