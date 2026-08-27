from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import selective_recall.core as core
from selective_recall import git_blob_sha_bytes, route_recall


class SelectiveRecallDAAttacks(unittest.TestCase):
    def build_registry(self, root: Path, *, irrelevant_count: int = 25) -> None:
        records = []
        for index in range(irrelevant_count):
            path = f"sources/irrelevant-{index:03d}.md"
            source = root / path
            source.parent.mkdir(parents=True, exist_ok=True)
            data = f"irrelevant {index}\n".encode()
            source.write_bytes(data)
            records.append(
                {
                    "memory_id": f"memory:irrelevant:{index:03d}",
                    "source_path": path,
                    "source_git_blob_sha": git_blob_sha_bytes(data),
                    "lifecycle_state": "ACTIVE_CANDIDATE",
                    "event_triggers": ["unrelated_event"],
                    "scope_tags": ["unrelated"],
                    "as_of": "2026-08-27T06:33:09Z",
                    "superseded_by": None,
                    "evidence_refs": [path],
                }
            )

        relevant_path = "sources/relevant.md"
        relevant_source = root / relevant_path
        relevant_source.parent.mkdir(parents=True, exist_ok=True)
        relevant_data = b"relevant source\n"
        relevant_source.write_bytes(relevant_data)
        records.append(
            {
                "memory_id": "memory:relevant",
                "source_path": relevant_path,
                "source_git_blob_sha": git_blob_sha_bytes(relevant_data),
                "lifecycle_state": "ACTIVE_CANDIDATE",
                "event_triggers": ["target_event"],
                "scope_tags": ["target"],
                "as_of": "2026-08-27T06:33:09Z",
                "superseded_by": None,
                "evidence_refs": [relevant_path],
            }
        )

        registry = {
            "schema_version": 1,
            "execution_authority": "NONE",
            "promotion_authority": "NONE",
            "records": records,
        }
        memory = root / "memory"
        memory.mkdir(parents=True, exist_ok=True)
        (memory / "recall_registry.json").write_text(
            json.dumps(registry, indent=2) + "\n", encoding="utf-8"
        )

    def request(self) -> dict:
        return {
            "event": "target_event",
            "scope_tags": ["target"],
            "current_context_sufficient": False,
            "explicit_recall": False,
            "max_results": 1,
        }

    def test_irrelevant_records_do_not_pay_source_hash_cost(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.build_registry(root, irrelevant_count=25)
            original = core.git_blob_sha_path
            calls: list[str] = []

            def counted(path: Path) -> str:
                calls.append(path.name)
                return original(path)

            with patch("selective_recall.core.git_blob_sha_path", side_effect=counted):
                result = route_recall(root, self.request())

            self.assertEqual(result["recall_decision"], "RECALL")
            self.assertEqual([a["memory_id"] for a in result["selected_anchors"]], ["memory:relevant"])
            self.assertEqual(calls, ["relevant.md"])

    def test_exclusion_diagnostics_are_aggregate_not_unbounded_identity_dump(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.build_registry(root, irrelevant_count=100)
            result = route_recall(root, self.request())

            self.assertEqual(result["recall_decision"], "RECALL")
            self.assertNotIn("excluded", result)
            self.assertEqual(result["excluded_count"], 100)
            self.assertEqual(result["exclusion_counts"], {"EVENT_MISMATCH": 100})

    def test_stale_irrelevant_record_is_classified_by_metadata_before_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.build_registry(root, irrelevant_count=1)
            registry_path = root / "memory" / "recall_registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["records"][0]["source_git_blob_sha"] = "0" * 40
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            result = route_recall(root, self.request())
            self.assertEqual(result["recall_decision"], "RECALL")
            self.assertEqual(result["exclusion_counts"], {"EVENT_MISMATCH": 1})

    def test_counter_da_relevant_stale_record_still_checks_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.build_registry(root, irrelevant_count=0)
            registry_path = root / "memory" / "recall_registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["records"][0]["source_git_blob_sha"] = "0" * 40
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            original = core.git_blob_sha_path
            calls: list[str] = []

            def counted(path: Path) -> str:
                calls.append(path.name)
                return original(path)

            with patch("selective_recall.core.git_blob_sha_path", side_effect=counted):
                result = route_recall(root, self.request())

            self.assertEqual(result["recall_decision"], "NO_RECALL")
            self.assertEqual(result["selected_anchors"], [])
            self.assertEqual(calls, ["relevant.md"])
            self.assertEqual(result["excluded_count"], 1)
            self.assertEqual(result["exclusion_counts"], {"STALE": 1})
            self.assertNotIn("excluded", result)

    def test_counter_da_scope_mismatch_stays_cold_and_non_authorizing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.build_registry(root, irrelevant_count=2)
            request = self.request()
            request["scope_tags"] = ["different-scope"]
            calls: list[str] = []

            with patch(
                "selective_recall.core.git_blob_sha_path",
                side_effect=lambda path: calls.append(path.name) or "0" * 40,
            ):
                result = route_recall(root, request)

            self.assertEqual(result["recall_decision"], "NO_RECALL")
            self.assertEqual(calls, [])
            self.assertEqual(result["excluded_count"], 3)
            self.assertEqual(
                result["exclusion_counts"],
                {"EVENT_MISMATCH": 2, "SCOPE_MISMATCH": 1},
            )
            self.assertEqual(result["execution_authority"], "NONE")
            self.assertEqual(result["promotion_authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
