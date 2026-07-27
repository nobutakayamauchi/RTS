from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError
from proof_engine_pilot.report_reader_usability import (
    verify_checkpoint,
    verify_confusion_log,
    verify_packet_v2,
    verify_progress_map,
    verify_protocol,
    verify_reader_usability_stage,
    verify_result,
    verify_review_v1,
    verify_review_v2,
)


class ReaderUsabilityTests(unittest.TestCase):
    def test_committed_stage_verifies(self) -> None:
        stage = verify_reader_usability_stage()
        self.assertEqual(stage["summary"]["rts_overall_planning_estimate_percent"], 74)
        self.assertEqual(stage["summary"]["short_term_internal_product_candidate_percent"], 97)
        self.assertEqual(stage["summary"]["current_step"], "HARD-004")
        self.assertFalse(stage["summary"]["external_human_review_performed"])

    def test_progress_authority_widening_fails(self) -> None:
        value = copy.deepcopy(verify_progress_map())
        value["authority"]["customer_pilot_authorized"] = True
        with self.assertRaises(ProofEngineError):
            verify_progress_map(value)

    def test_progress_jump_fails(self) -> None:
        value = copy.deepcopy(verify_progress_map())
        value["current_position"]["short_term_completion_percent"] = 100
        with self.assertRaises(ProofEngineError):
            verify_progress_map(value)

    def test_protocol_external_human_claim_fails(self) -> None:
        value = copy.deepcopy(verify_protocol())
        value["authority"]["external_human_claim_authorized"] = True
        with self.assertRaises(ProofEngineError):
            verify_protocol(value)

    def test_review_v1_confusion_deletion_fails(self) -> None:
        value = copy.deepcopy(verify_review_v1())
        value["reader_results"][0]["material_confusions"] = []
        with self.assertRaises(ProofEngineError):
            verify_review_v1(value)

    def test_confusion_log_raw_input_fails(self) -> None:
        value = copy.deepcopy(verify_confusion_log())
        value["raw_user_input_included"] = True
        with self.assertRaises(ProofEngineError):
            verify_confusion_log(value)

    def test_packet_v2_loses_withheld_section_fails(self) -> None:
        value = copy.deepcopy(verify_packet_v2())
        value["plain_language_status"]["not_verified"] = []
        with self.assertRaises(ProofEngineError):
            verify_packet_v2(value)

    def test_packet_v2_manufactures_external_validation_fails(self) -> None:
        value = copy.deepcopy(verify_packet_v2())
        value["external_human_validation_claimed"] = True
        with self.assertRaises(ProofEngineError):
            verify_packet_v2(value)

    def test_review_v2_wrong_answer_fails(self) -> None:
        value = copy.deepcopy(verify_review_v2())
        value["reader_results"][1]["correct_answers"] = 5
        with self.assertRaises(ProofEngineError):
            verify_review_v2(value)

    def test_review_v2_commercial_inference_fails(self) -> None:
        value = copy.deepcopy(verify_review_v2())
        value["reader_results"][2]["commercial_inference_rejected"] = False
        with self.assertRaises(ProofEngineError):
            verify_review_v2(value)

    def test_result_customer_authority_fails(self) -> None:
        value = copy.deepcopy(verify_result())
        value["authority"]["customer_intake_authorized"] = True
        with self.assertRaises(ProofEngineError):
            verify_result(value)

    def test_result_wrong_next_gate_fails(self) -> None:
        value = copy.deepcopy(verify_result())
        value["next_gate"] = "CUSTOMER_PILOT"
        with self.assertRaises(ProofEngineError):
            verify_result(value)

    def test_checkpoint_external_action_fails(self) -> None:
        value = copy.deepcopy(verify_checkpoint())
        value["publication_performed"] = True
        with self.assertRaises(ProofEngineError):
            verify_checkpoint(value)


if __name__ == "__main__":
    unittest.main()
