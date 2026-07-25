from __future__ import annotations

import unittest

from loop_core.cli import validate_learning_index_boundary
from loop_core.models import LoopCoreError


class LoopCoreLearningLifecycleTests(unittest.TestCase):
    def test_frozen_learning_child_remains_unapproved(self) -> None:
        self.assertFalse(
            validate_learning_index_boundary(
                {
                    "status": "FROZEN",
                    "build_authority": "NOT_APPROVED",
                    "preflight_state": "PASS",
                }
            )
        )

    def test_active_learning_child_requires_current_gate_validation(self) -> None:
        for status in ("SELECTED", "IN_PROGRESS", "VERIFIED", "COMPLETED"):
            with self.subTest(status=status):
                self.assertTrue(
                    validate_learning_index_boundary(
                        {
                            "status": status,
                            "build_authority": "APPROVED",
                            "preflight_state": "PASS",
                        }
                    )
                )

    def test_active_learning_child_without_approval_fails_closed(self) -> None:
        with self.assertRaisesRegex(LoopCoreError, "build_authority=APPROVED"):
            validate_learning_index_boundary(
                {
                    "status": "IN_PROGRESS",
                    "build_authority": "NOT_APPROVED",
                    "preflight_state": "PASS",
                }
            )

    def test_active_learning_child_without_pass_preflight_fails_closed(self) -> None:
        with self.assertRaisesRegex(LoopCoreError, "preflight_state=PASS"):
            validate_learning_index_boundary(
                {
                    "status": "IN_PROGRESS",
                    "build_authority": "APPROVED",
                    "preflight_state": "STALE",
                }
            )

    def test_unsupported_learning_status_fails_closed(self) -> None:
        with self.assertRaisesRegex(LoopCoreError, "unsupported governed status"):
            validate_learning_index_boundary(
                {
                    "status": "READY",
                    "build_authority": "APPROVED",
                    "preflight_state": "PASS",
                }
            )


if __name__ == "__main__":
    unittest.main()
