from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from outcome_evidence.corpus import corpus_summary, load_corpus
from outcome_evidence.models import (
    OutcomeEvidenceError,
    bundle_material,
    load_json,
    sha256_value,
    validate_bundle,
)


class OutcomeEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        source = Path(__file__).resolve().parents[1] / "outcome_evidence"
        shutil.copytree(source, self.root / "outcome_evidence")

    def _bundle_path(self, scenario: str) -> Path:
        return self.root / "outcome_evidence" / "examples" / f"{scenario.lower()}.json"

    def _read(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def _write(self, path: Path, value) -> None:
        path.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_committed_corpus_verifies_with_required_variation(self) -> None:
        bundles = load_corpus(self.root)
        self.assertGreaterEqual(len(bundles), 3)
        self.assertTrue({"SUCCESS", "ESCALATION", "RECOVERY"} <= {b["scenario"] for b in bundles})
        self.assertTrue(all(b["execution_scope"] == "SIMULATED_ONLY" for b in bundles))
        self.assertTrue(all(b["promotion_eligibility"] == "NOT_ELIGIBLE" for b in bundles))

    def test_summary_is_deterministic(self) -> None:
        self.assertEqual(corpus_summary(self.root), corpus_summary(self.root))

    def test_bundle_fingerprint_mutation_fails_closed(self) -> None:
        path = self._bundle_path("SUCCESS")
        bundle = self._read(path)
        bundle["classification_rationale"] = "mutated"
        self._write(path, bundle)
        with self.assertRaisesRegex(OutcomeEvidenceError, "fingerprint mismatch"):
            load_corpus(self.root)

    def test_evidence_hash_mutation_fails_closed(self) -> None:
        evidence = self.root / "outcome_evidence" / "evidence" / "success-controller-result.json"
        evidence.write_text(evidence.read_text(encoding="utf-8") + " ", encoding="utf-8")
        with self.assertRaisesRegex(OutcomeEvidenceError, "evidence hash mismatch"):
            load_corpus(self.root)

    def test_external_execution_claim_fails_closed(self) -> None:
        bundle = self._read(self._bundle_path("SUCCESS"))
        bundle["controller"]["external_execution_performed"] = True
        with self.assertRaisesRegex(OutcomeEvidenceError, "external execution claims"):
            validate_bundle(bundle)

    def test_simulated_success_cannot_claim_verified(self) -> None:
        bundle = self._read(self._bundle_path("SUCCESS"))
        bundle["outcome_classification"] = "VERIFIED"
        with self.assertRaisesRegex(OutcomeEvidenceError, "SUCCESS classification"):
            validate_bundle(bundle)

    def test_promotion_eligibility_cannot_be_widened(self) -> None:
        bundle = self._read(self._bundle_path("ESCALATION"))
        bundle["promotion_eligibility"] = "ELIGIBLE"
        with self.assertRaisesRegex(OutcomeEvidenceError, "never promotion eligible"):
            validate_bundle(bundle)

    def test_private_content_field_fails_closed(self) -> None:
        bundle = self._read(self._bundle_path("RECOVERY"))
        bundle["execution_record"]["result"]["secret_value"] = "redacted"
        with self.assertRaises(OutcomeEvidenceError):
            validate_bundle(bundle)

    def test_evidence_path_traversal_fails_closed(self) -> None:
        bundle = self._read(self._bundle_path("SUCCESS"))
        bundle["evidence_refs"][0]["source_ref"] = "../outside.json"
        with self.assertRaisesRegex(OutcomeEvidenceError, "repository-relative"):
            validate_bundle(bundle)

    def test_duplicate_bundle_id_fails_closed(self) -> None:
        source = self._bundle_path("SUCCESS")
        duplicate = self.root / "outcome_evidence" / "examples" / "success-copy.json"
        shutil.copyfile(source, duplicate)
        with self.assertRaisesRegex(OutcomeEvidenceError, "duplicate bundle IDs"):
            load_corpus(self.root)

    def test_missing_required_scenario_fails_closed(self) -> None:
        self._bundle_path("RECOVERY").unlink()
        with self.assertRaisesRegex(OutcomeEvidenceError, "at least three bundles|missing scenarios"):
            load_corpus(self.root)

    def test_evidence_controller_disagreement_fails_closed(self) -> None:
        path = self.root / "outcome_evidence" / "evidence" / "escalation-controller-result.json"
        evidence = load_json(path)
        evidence["terminal_state"] = "FAILED"
        self._write(path, evidence)
        bundle_path = self._bundle_path("ESCALATION")
        bundle = self._read(bundle_path)
        bundle["evidence_integrity"][evidence["evidence_id"]] = hashlib.sha256(path.read_bytes()).hexdigest()
        bundle["bundle_fingerprint"] = sha256_value(bundle_material(bundle))
        self._write(bundle_path, bundle)
        with self.assertRaisesRegex(OutcomeEvidenceError, "evidence/controller mismatch"):
            load_corpus(self.root)


if __name__ == "__main__":
    unittest.main()
