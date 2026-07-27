from __future__ import annotations

import copy
import inspect
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint
from proof_engine_pilot import report_customer_pilot_plan as stage


def resign(value: dict, field: str) -> dict:
    value = copy.deepcopy(value)
    value.pop(field, None)
    value[field] = fingerprint(value)
    return value


class CustomerPilotPlanTests(unittest.TestCase):
    def test_valid_stage(self) -> None:
        result = stage.verify_customer_pilot_plan_stage()
        self.assertEqual(result["summary"]["state"], "INTERNAL_BOUNDED_CUSTOMER_PILOT_PLAN_REVIEW_COMPLETE")
        self.assertFalse(result["summary"]["customer_pilot_execution_authorized"])

    def test_plan_limits_are_exactly_one(self) -> None:
        value = stage.verify_contract()
        value = copy.deepcopy(value)
        value["pilot_shape"]["participant_limit"] = 2
        value = resign(value, "contract_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_contract(value)

    def test_commercial_consideration_fails(self) -> None:
        value = stage.verify_contract()
        value = copy.deepcopy(value)
        value["pilot_shape"]["commercial_consideration_authorized"] = True
        value = resign(value, "contract_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_contract(value)

    def test_execution_authority_fails(self) -> None:
        value = stage.verify_contract()
        value = copy.deepcopy(value)
        value["authority"]["customer_pilot_execution_authorized"] = True
        value = resign(value, "contract_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_contract(value)

    def test_participant_selection_manufacture_fails(self) -> None:
        value = stage.verify_eligibility()
        value = copy.deepcopy(value)
        value["real_participant_selected"] = True
        value = resign(value, "eligibility_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_eligibility(value)

    def test_consent_weakening_fails(self) -> None:
        value = stage.verify_eligibility()
        value = copy.deepcopy(value)
        value["required_profile"]["consent"] = "IMPLIED"
        value = resign(value, "eligibility_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_eligibility(value)

    def test_private_source_allowance_fails(self) -> None:
        value = stage.verify_data_boundary()
        value = copy.deepcopy(value)
        value["allowed_planned_inputs"].append("private repository")
        value = resign(value, "boundary_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_data_boundary(value)

    def test_raw_prohibited_retention_fails(self) -> None:
        value = stage.verify_data_boundary()
        value = copy.deepcopy(value)
        value["retention_policy"]["raw_prohibited_payload_retained"] = True
        value = resign(value, "boundary_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_data_boundary(value)

    def test_secret_routing_weakening_fails(self) -> None:
        value = stage.verify_data_boundary()
        value = copy.deepcopy(value)
        value["routing_policy"]["credential_or_secret"] = "MASK"
        value = resign(value, "boundary_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_data_boundary(value)

    def test_required_success_weakening_fails(self) -> None:
        value = stage.verify_scorecard()
        value = copy.deepcopy(value)
        value["success_criteria"][0]["required"] = False
        value = resign(value, "scorecard_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_scorecard(value)

    def test_partial_success_fails(self) -> None:
        value = stage.verify_scorecard()
        value = copy.deepcopy(value)
        value["partial_success_prohibited"] = False
        value = resign(value, "scorecard_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_scorecard(value)

    def test_failure_condition_deletion_fails(self) -> None:
        value = stage.verify_scorecard()
        value = copy.deepcopy(value)
        value["failure_conditions"] = value["failure_conditions"][:-1]
        value = resign(value, "scorecard_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_scorecard(value)

    def test_incident_raw_log_fails(self) -> None:
        value = stage.verify_incident_runbook()
        value = copy.deepcopy(value)
        value["no_raw_payload_in_incident_log"] = False
        value = resign(value, "runbook_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_incident_runbook(value)

    def test_automatic_resume_fails(self) -> None:
        value = stage.verify_incident_runbook()
        value = copy.deepcopy(value)
        value["automatic_resume"] = True
        value = resign(value, "runbook_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_incident_runbook(value)

    def test_readiness_score_inflation_fails(self) -> None:
        value = stage.verify_score_hold()
        value = copy.deepcopy(value)
        value["current_product_readiness_score"] = 94
        value["score_change"] = 1
        value = resign(value, "decision_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_score_hold(value)

    def test_customer_value_claim_deletion_fails(self) -> None:
        value = stage.verify_score_hold()
        value = copy.deepcopy(value)
        value["not_supported"].remove("CUSTOMER_VALUE_VALIDATED")
        value = resign(value, "decision_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_score_hold(value)

    def test_review_criterion_deletion_fails(self) -> None:
        value = stage.verify_plan_review()
        value = copy.deepcopy(value)
        value["criteria_results"] = value["criteria_results"][:-1]
        value = resign(value, "review_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_plan_review(value)

    def test_contact_manufacture_fails(self) -> None:
        value = stage.verify_plan_review()
        value = copy.deepcopy(value)
        value["participant_contact_performed"] = True
        value = resign(value, "review_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_plan_review(value)

    def test_completion_execution_widening_fails(self) -> None:
        value = stage.verify_completion()
        value = copy.deepcopy(value)
        value["execution_status"] = "AUTHORIZED"
        value = resign(value, "completion_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_completion(value)

    def test_progress_execution_manufacture_fails(self) -> None:
        value = stage.verify_progress()
        value = copy.deepcopy(value)
        value["current_position"]["pilot_execution_authorized"] = True
        value = resign(value, "map_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_progress(value)

    def test_checkpoint_external_action_fails(self) -> None:
        value = stage.verify_checkpoint()
        value = copy.deepcopy(value)
        value["outreach_performed"] = True
        value = resign(value, "checkpoint_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_checkpoint(value)

    def test_verifier_is_read_only(self) -> None:
        source = inspect.getsource(stage)
        forbidden = ["subprocess", "requests.", "urllib.", ".write_text(", ".write_bytes(", "os.system", "git push", "gh pr"]
        self.assertFalse(any(item in source for item in forbidden))


if __name__ == "__main__":
    unittest.main()
