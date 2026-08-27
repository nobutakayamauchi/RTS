from __future__ import annotations

import ast
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from selective_recall import (
    LIFECYCLE_STATES,
    RecallValidationError,
    git_blob_sha_bytes,
    route_recall,
    validate_transition,
    verify_registry,
)


class SelectiveRecallV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[1]

    def request(
        self,
        *,
        event: str = "context_loss",
        scopes: list[str] | None = None,
        sufficient: bool = False,
        explicit: bool = False,
        max_results: int = 1,
    ) -> dict:
        return {
            "event": event,
            "scope_tags": scopes or [],
            "current_context_sufficient": sufficient,
            "explicit_recall": explicit,
            "max_results": max_results,
        }

    def write_temp_registry(
        self,
        root: Path,
        *,
        state: str = "ACTIVE_CANDIDATE",
        superseded_by: str | None = None,
        source_path: str = "memory_source.md",
        memory_id: str = "memory:test",
        sha_override: str | None = None,
    ) -> Path:
        data = b"bounded memory source\n"
        source = root / source_path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(data)
        registry = {
            "schema_version": 1,
            "execution_authority": "NONE",
            "promotion_authority": "NONE",
            "records": [
                {
                    "memory_id": memory_id,
                    "source_path": source_path,
                    "source_git_blob_sha": sha_override or git_blob_sha_bytes(data),
                    "lifecycle_state": state,
                    "event_triggers": ["context_loss"],
                    "scope_tags": ["context", "reconstruction"],
                    "as_of": "2026-08-27T06:33:09Z",
                    "superseded_by": superseded_by,
                    "evidence_refs": [source_path],
                }
            ],
        }
        registry_path = root / "memory" / "recall_registry.json"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        return registry_path

    def test_committed_registry_is_current_and_non_authorizing(self) -> None:
        result = verify_registry(self.repo_root)
        self.assertEqual(result["record_count"], 2)
        self.assertTrue(result["all_sources_current"])
        self.assertEqual(result["execution_authority"], "NONE")
        self.assertEqual(result["promotion_authority"], "NONE")

    def test_no_recall_fast_path_does_not_require_registry(self) -> None:
        result = route_recall(
            self.repo_root,
            self.request(sufficient=True),
            registry_path="memory/definitely-missing-registry.json",
        )
        self.assertEqual(result["recall_decision"], "NO_RECALL")
        self.assertEqual(result["reason"], "CURRENT_CONTEXT_SUFFICIENT")
        self.assertEqual(result["selected_anchors"], [])

    def test_insufficient_signal_does_not_guess_or_require_registry(self) -> None:
        result = route_recall(
            self.repo_root,
            self.request(event="", sufficient=False),
            registry_path="memory/definitely-missing-registry.json",
        )
        self.assertEqual(result["recall_decision"], "NO_RECALL")
        self.assertEqual(result["reason"], "INSUFFICIENT_SIGNAL")

    def test_event_and_scope_select_only_relevant_smallest_anchor(self) -> None:
        result = route_recall(
            self.repo_root,
            self.request(
                event="reasoning_continuity_loss",
                scopes=["context", "claude-code"],
                max_results=1,
            ),
        )
        self.assertEqual(result["recall_decision"], "RECALL")
        self.assertEqual(len(result["selected_anchors"]), 1)
        anchor = result["selected_anchors"][0]
        self.assertEqual(
            anchor["memory_id"],
            "incident:INC_20260222_1603_ClaudeCode_ContextLoss.md",
        )
        self.assertEqual(anchor["freshness"], "CURRENT")
        for forbidden in ("body", "content", "snippet", "text"):
            self.assertNotIn(forbidden, anchor)

    def test_max_results_and_tie_order_are_deterministic(self) -> None:
        first = route_recall(
            self.repo_root,
            self.request(event="context_loss", scopes=["context"], max_results=1),
        )
        second = route_recall(
            self.repo_root,
            self.request(event="context_loss", scopes=["context"], max_results=1),
        )
        self.assertEqual(first, second)
        self.assertEqual(len(first["selected_anchors"]), 1)
        self.assertEqual(
            first["selected_anchors"][0]["memory_id"],
            "incident:INC_20260222_1545_Cursor_ContextLoss.md",
        )

    def test_stale_source_is_excluded_from_recall(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.write_temp_registry(root)
            (root / "memory_source.md").write_text("changed after registry\n", encoding="utf-8")
            result = route_recall(root, self.request())
            self.assertEqual(result["recall_decision"], "NO_RECALL")
            self.assertEqual(result["selected_anchors"], [])
            self.assertEqual(result["excluded_count"], 1)
            self.assertEqual(result["exclusion_counts"], {"STALE": 1})
            with self.assertRaises(RecallValidationError):
                verify_registry(root, require_current=True)

    def test_superseded_record_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.write_temp_registry(
                root,
                state="CANONICAL",
                superseded_by="memory:newer",
            )
            result = route_recall(root, self.request())
            self.assertEqual(result["recall_decision"], "NO_RECALL")
            self.assertEqual(result["selected_anchors"], [])

    def test_quarantined_record_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.write_temp_registry(root, state="QUARANTINED")
            result = route_recall(root, self.request())
            self.assertEqual(result["recall_decision"], "NO_RECALL")
            self.assertEqual(result["selected_anchors"], [])

    def test_raw_record_is_not_default_active_recall(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.write_temp_registry(root, state="RAW")
            result = route_recall(root, self.request())
            self.assertEqual(result["recall_decision"], "NO_RECALL")

    def test_duplicate_memory_ids_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry_path = self.write_temp_registry(root)
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["records"].append(dict(registry["records"][0]))
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaises(RecallValidationError):
                verify_registry(root, require_current=False)

    def test_path_escape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry_path = self.write_temp_registry(root)
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["records"][0]["source_path"] = "../outside.md"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaises(RecallValidationError):
                verify_registry(root, require_current=False)

    def test_registry_authority_must_remain_none(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry_path = self.write_temp_registry(root)
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["execution_authority"] = "APPROVED"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaises(RecallValidationError):
                verify_registry(root, require_current=False)

    def test_every_recall_output_is_non_authorizing(self) -> None:
        for request in (
            self.request(sufficient=True),
            self.request(event=""),
            self.request(event="context_loss", scopes=["context"], max_results=2),
        ):
            result = route_recall(self.repo_root, request)
            self.assertEqual(result["execution_authority"], "NONE")
            self.assertEqual(result["promotion_authority"], "NONE")

    def test_lifecycle_vocabulary_is_exact(self) -> None:
        self.assertEqual(
            LIFECYCLE_STATES,
            {
                "RAW",
                "ACTIVE_CANDIDATE",
                "VERIFICATION_PENDING",
                "REPEATED",
                "PROMOTION_READY",
                "CANONICAL",
                "FOLDED",
                "SUPERSEDED",
                "ARCHIVED",
                "QUARANTINED",
            },
        )

    def test_direct_raw_to_canonical_is_rejected(self) -> None:
        with self.assertRaises(RecallValidationError):
            validate_transition("RAW", "CANONICAL")

    def test_staged_transition_validates_but_does_not_apply(self) -> None:
        result = validate_transition("RAW", "ACTIVE_CANDIDATE")
        self.assertTrue(result["valid"])
        self.assertFalse(result["applied"])
        self.assertEqual(result["application_authority"], "NONE")
        self.assertEqual(result["execution_authority"], "NONE")
        self.assertEqual(result["promotion_authority"], "NONE")

    def test_routing_does_not_mutate_registry_index_or_seed_sources(self) -> None:
        watched = [
            self.repo_root / "memory" / "recall_registry.json",
            self.repo_root / "memory" / "index.json",
            self.repo_root / "incidents" / "INC_20260222_1545_Cursor_ContextLoss.md",
            self.repo_root / "incidents" / "INC_20260222_1603_ClaudeCode_ContextLoss.md",
        ]
        before = {path: path.read_bytes() for path in watched}
        route_recall(
            self.repo_root,
            self.request(event="context_loss", scopes=["context"], max_results=2),
        )
        after = {path: path.read_bytes() for path in watched}
        self.assertEqual(before, after)

    def test_package_has_no_forbidden_external_action_imports(self) -> None:
        forbidden = {
            "subprocess",
            "socket",
            "requests",
            "httpx",
            "urllib",
            "paramiko",
            "boto3",
            "stripe",
        }
        seen: set[str] = set()
        package = self.repo_root / "selective_recall"
        for path in package.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    seen.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    seen.add(node.module.split(".")[0])
        self.assertTrue(forbidden.isdisjoint(seen), seen & forbidden)

    def test_child_a_lifecycle_boundary_is_governed(self) -> None:
        items = {}
        active = []
        for current in (self.repo_root / "freezer" / "items").glob("RTS-FRZ-*/current.json"):
            pointer = json.loads(current.read_text(encoding="utf-8"))
            item = json.loads((self.repo_root / pointer["path"]).read_text(encoding="utf-8"))
            items[item["item_id"]] = item
            if item["status"] == "IN_PROGRESS":
                active.append(item["item_id"])

        child = items["RTS-FRZ-000011"]
        self.assertIn(child["status"], {"IN_PROGRESS", "VERIFIED", "COMPLETED"})
        if child["status"] == "IN_PROGRESS":
            self.assertEqual(active, ["RTS-FRZ-000011"])
            for item_id in ("RTS-FRZ-000012", "RTS-FRZ-000013", "RTS-FRZ-000014", "RTS-FRZ-000015"):
                self.assertEqual(items[item_id]["status"], "FROZEN")
                self.assertEqual(items[item_id]["build_authority"], "NOT_APPROVED")
        else:
            self.assertNotIn("RTS-FRZ-000011", active)


if __name__ == "__main__":
    unittest.main()
