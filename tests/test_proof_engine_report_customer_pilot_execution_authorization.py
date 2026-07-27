from __future__ import annotations

import copy
import inspect
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint
from proof_engine_pilot import report_customer_pilot_execution_authorization as stage


def resign(value: dict, field: str) -> dict:
    value = copy.deepcopy(value)
    value.pop(field, None)
    value[field] = fingerprint(value)
    return value


class CustomerPilotExecutionAuthorizationTests(unittest.TestCase):
    def test_valid_stage(self) -> None:
        result = stage.verify_customer_pilot_execution_authorization_stage()
        self.assertEqual(result["summary"]["state"], "INTERNAL_BOUNDED_CUSTOMER_PILOT_EXECUTION_AUTHORIZATION_PACKET_COMPLETE")
        self.assertEqual(result["summary"]["candidate_count"], 0)
        self.assertFalse(result["summary"]["participant_contact_authorized"])

    def test_prior_plan_history_is_intact(self) -> None:
        prior = stage.verify_prior_plan_history()
        self.assertEqual(prior["prior_status"], stage.PRIOR_STATUS_FP)
        self.assertEqual(prior["prior_checkpoint"], stage.PRIOR_CHECKPOINT_FP)

    def test_contract_scope_widening_fails(self) -> None:
        value = stage.verify_contract()
        value = copy.deepcopy(value)
        value["scope"]["participant_limit"] = 2
        value = resign(value, "contract_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_contract(value)

    def test_contract_contact_authority_fails(self) -> None:
        value = stage.verify_contract()
        value = copy.deepcopy(value)
        value["authorized_now"]["named_candidate_contact"] = True
        value = resign(value, "contract_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_contract(value)

    def test_contract_score_inflation_fails(self) -> None:
        value = stage.verify_contract()
        value = copy.deepcopy(value)
        value["acceptance"]["product_readiness_score_required"] = 94
        value = resign(value, "contract_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_contract(value)

    def test_candidate_injection_fails(self) -> None:
        value = stage.verify_scorecard()
        value = copy.deepcopy(value)
        value["candidate_records"] = [{"name": "someone"}]
        value["candidate_count"] = 1
        value = resign(value, "scorecard_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_scorecard(value)

    def test_candidate_threshold_weakening_fails(self) -> None:
        value = stage.verify_scorecard()
        value = copy.deepcopy(value)
        value["threshold"]["minimum_score"] = 50
        value = resign(value, "scorecard_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_scorecard(value)

    def test_hard_gate_removal_fails(self) -> None:
        value = stage.verify_scorecard()
        value = copy.deepcopy(value)
        value["hard_gates"] = value["hard_gates"][:-1]
        value = resign(value, "scorecard_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_scorecard(value)

    def test_outreach_send_status_fails(self) -> None:
        value = stage.verify_outreach()
        value = copy.deepcopy(value)
        value["send_status"] = "SENT"
        value = resign(value, "template_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_outreach(value)

    def test_outreach_named_recipient_fails(self) -> None:
        value = stage.verify_outreach()
        value = copy.deepcopy(value)
        value["named_recipient"] = "candidate"
        value = resign(value, "template_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_outreach(value)

    def test_outreach_disclosure_removal_fails(self) -> None:
        value = stage.verify_outreach()
        value = copy.deepcopy(value)
        value["body"] = value["body"].replace("返信だけでは分析を開始しません", "返信後に開始します")
        value = resign(value, "template_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_outreach(value)

    def test_consent_submission_fails(self) -> None:
        value = stage.verify_consent()
        value = copy.deepcopy(value)
        value["submission_count"] = 1
        value = resign(value, "form_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_consent(value)

    def test_consent_confirmation_removal_fails(self) -> None:
        value = stage.verify_consent()
        value = copy.deepcopy(value)
        value["required_confirmations"] = value["required_confirmations"][:-1]
        value = resign(value, "form_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_consent(value)

    def test_ambiguous_consent_acceptance_fails(self) -> None:
        value = stage.verify_consent()
        value = copy.deepcopy(value)
        value["consent_validity"]["blank_or_ambiguous_value"] = "ACCEPT"
        value = resign(value, "form_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_consent(value)

    def test_private_source_constraint_fails(self) -> None:
        value = stage.verify_source_freeze()
        value = copy.deepcopy(value)
        value["required_fields"][1]["constraint"] = "PRIVATE"
        value = resign(value, "form_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_source_freeze(value)

    def test_source_already_frozen_fails(self) -> None:
        value = stage.verify_source_freeze()
        value = copy.deepcopy(value)
        value["source_freeze_count"] = 1
        value = resign(value, "form_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_source_freeze(value)

    def test_partial_preflight_fails(self) -> None:
        value = stage.verify_preflight()
        value = copy.deepcopy(value)
        value["partial_pass_allowed"] = True
        value = resign(value, "checklist_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_preflight(value)

    def test_preflight_false_completion_fails(self) -> None:
        value = stage.verify_preflight()
        value = copy.deepcopy(value)
        value["completed_check_count"] = 16
        value = resign(value, "checklist_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_preflight(value)

    def test_preflight_check_removal_fails(self) -> None:
        value = stage.verify_preflight()
        value = copy.deepcopy(value)
        value["checks"] = value["checks"][:-1]
        value = resign(value, "checklist_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_preflight(value)

    def test_incident_count_fails(self) -> None:
        value = stage.verify_withdrawal()
        value = copy.deepcopy(value)
        value["incident_count"] = 1
        value = resign(value, "protocol_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_withdrawal(value)

    def test_withdrawal_restart_weakening_fails(self) -> None:
        value = stage.verify_withdrawal()
        value = copy.deepcopy(value)
        value["withdrawal_effect"]["restart"] = "automatic"
        value = resign(value, "protocol_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_withdrawal(value)

    def test_decision_contact_authority_fails(self) -> None:
        value = stage.verify_decision()
        value = copy.deepcopy(value)
        value["authority"]["participant_contact_authorized"] = True
        value = resign(value, "decision_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_decision(value)

    def test_decision_external_evidence_fails(self) -> None:
        value = stage.verify_decision()
        value = copy.deepcopy(value)
        value["external_evidence_created"] = True
        value = resign(value, "decision_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_decision(value)

    def test_decision_score_inflation_fails(self) -> None:
        value = stage.verify_decision()
        value = copy.deepcopy(value)
        value["product_readiness_score"] = 94
        value = resign(value, "decision_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_decision(value)

    def test_progress_contact_authority_fails(self) -> None:
        value = stage.verify_progress()
        value = copy.deepcopy(value)
        value["current_position"]["participant_contact_authorized"] = True
        value = resign(value, "map_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_progress(value)

    def test_checkpoint_external_action_fails(self) -> None:
        value = stage.verify_checkpoint()
        value = copy.deepcopy(value)
        value["participant_contact_performed"] = True
        value = resign(value, "checkpoint_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_checkpoint(value)

    def test_verifier_is_read_only(self) -> None:
        source = inspect.getsource(stage)
        forbidden = ["subprocess", "requests.", "urllib.", ".write_text(", ".write_bytes(", "os.system", "git push", "gh pr"]
        self.assertFalse(any(item in source for item in forbidden))


if __name__ == "__main__":
    unittest.main()
