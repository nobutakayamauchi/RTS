from __future__ import annotations

import copy
import inspect
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint
from proof_engine_pilot import report_privacy_hardening as stage


def resign(value: dict, field: str) -> dict:
    value = copy.deepcopy(value)
    value.pop(field, None)
    value[field] = fingerprint(value)
    return value


class PrivacyHardeningTests(unittest.TestCase):
    def test_valid_stage_reaches_bounded_internal_completion(self) -> None:
        result = stage.verify_privacy_hardening_stage()
        self.assertEqual(result["summary"]["short_term_completion_percent"], 100)
        self.assertEqual(result["summary"]["product_readiness_score"], 93)
        self.assertFalse(result["summary"]["customer_pilot_authorized"])

    def test_scanner_routes_stop_exclude_mask_and_allow(self) -> None:
        self.assertEqual(stage.scan_text("password=EXAMPLE_ONLY_PASSWORD_123")["action"], "STOP")
        self.assertEqual(stage.scan_text("個人番号 1234-5678-9012")["action"], "EXCLUDE")
        masked = stage.scan_text("email taro@example.jp")
        self.assertEqual(masked["action"], "MASK")
        self.assertNotIn("taro@example.jp", masked["sanitized_output"])
        self.assertEqual(stage.scan_text("公開PR #10")["action"], "ALLOW")

    def test_first_probe_records_two_real_corrections(self) -> None:
        value = stage.verify_probe_v1()
        self.assertEqual(value["failed_fixture_ids"], ["P-009", "P-012"])
        self.assertEqual(value["failure_count"], 2)

    def test_second_probe_has_zero_failures_and_residuals(self) -> None:
        value = stage.verify_probe_v2()
        self.assertEqual(value["failure_count"], 0)
        self.assertEqual(sum(len(item["residual_findings"]) for item in value["results"]), 0)
        self.assertEqual(value["protected_raw_payloads_persisted"], 0)

    def test_credential_downgrade_fails_closed(self) -> None:
        value = copy.deepcopy(stage.verify_probe_v2())
        item = next(item for item in value["results"] if item["fixture_id"] == "P-006")
        item["actual_action"] = "MASK"
        value = resign(value, "probe_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_probe_v2(value)

    def test_residual_personal_data_fails_closed(self) -> None:
        value = copy.deepcopy(stage.verify_probe_v2())
        item = next(item for item in value["results"] if item["fixture_id"] == "P-002")
        item["sanitized_output"] = "email taro.yamada@example.jp"
        item["sanitized_output_fingerprint"] = fingerprint(item["sanitized_output"])
        item["residual_findings"] = ["EMAIL"]
        value = resign(value, "probe_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_probe_v2(value)

    def test_raw_input_retention_fails_closed(self) -> None:
        value = copy.deepcopy(stage.verify_probe_v2())
        value["results"][0]["raw_input_included"] = True
        value = resign(value, "probe_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_probe_v2(value)

    def test_correction_deletion_fails_closed(self) -> None:
        value = copy.deepcopy(stage.verify_correction_log())
        value["entries"] = value["entries"][:1]
        value["correction_count"] = 1
        value = resign(value, "log_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_correction_log(value)

    def test_elapsed_measurement_tamper_fails_closed(self) -> None:
        value = copy.deepcopy(stage.verify_metrics())
        value["automated_benchmark"]["elapsed_nanoseconds"] = 1
        value = resign(value, "metrics_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_metrics(value)

    def test_manual_work_measurement_tamper_fails_closed(self) -> None:
        value = copy.deepcopy(stage.verify_metrics())
        value["operator_process"]["manual_steps"] = 0
        value = resign(value, "metrics_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_metrics(value)

    def test_readiness_score_inflation_fails_closed(self) -> None:
        value = copy.deepcopy(stage.verify_reassessment())
        value["weighted_score"] = 100
        value["score_change_from_baseline"] = 18
        value = resign(value, "assessment_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_reassessment(value)

    def test_customer_pilot_overclaim_fails_closed(self) -> None:
        value = copy.deepcopy(stage.verify_reassessment())
        value["customer_pilot_ready"] = True
        value["terminal"]["customer_pilot_status"] = "AUTHORIZED"
        value = resign(value, "assessment_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_reassessment(value)

    def test_short_term_completion_drift_fails_closed(self) -> None:
        value = copy.deepcopy(stage.verify_completion())
        value["short_term_completion_percent"] = 99
        value = resign(value, "completion_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_completion(value)

    def test_authority_widening_fails_closed(self) -> None:
        value = copy.deepcopy(stage.verify_progress())
        value["authority"]["pricing_authorized"] = True
        value = resign(value, "map_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_progress(value)

    def test_checkpoint_external_action_fails_closed(self) -> None:
        value = copy.deepcopy(stage.verify_checkpoint())
        value["publication_performed"] = True
        value = resign(value, "checkpoint_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_checkpoint(value)

    def test_fixture_pack_is_synthetic_only(self) -> None:
        value = stage.verify_fixtures()
        self.assertTrue(value["synthetic_only"])
        self.assertFalse(value["contains_real_personal_data"])
        self.assertFalse(value["contains_real_credentials"])

    def test_verifier_is_read_only(self) -> None:
        source = inspect.getsource(stage)
        forbidden = ["subprocess", "requests.", "urllib.", ".write_text(", ".write_bytes(", "os.system", "git push", "gh pr"]
        self.assertFalse(any(item in source for item in forbidden))


if __name__ == "__main__":
    unittest.main()
