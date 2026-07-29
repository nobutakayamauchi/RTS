from __future__ import annotations

import copy
import unittest
from pathlib import Path
from unittest.mock import patch

from proof_engine_pilot.core import ProofEngineError, fingerprint, load
import proof_engine_pilot.report_customer_pilot_named_candidate_contact_packet as M


def resign(value: dict, field: str) -> dict:
    result = copy.deepcopy(value)
    result.pop(field, None)
    result[field] = fingerprint(result)
    return result


class NamedCandidateContactPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load(M.PATH["contract"])
        self.selection = load(M.PATH["selection"])
        self.route = load(M.PATH["route"])
        self.message = load(M.PATH["message"])
        self.preflight = load(M.PATH["preflight"])
        self.response = load(M.PATH["response"])
        self.score_hold = load(M.PATH["score_hold"])
        self.completion = load(M.PATH["completion"])
        self.status = load(M.PATH["status"])
        self.checkpoint = load(M.PATH["checkpoint"])

    def semantic_failure(self, key: str, field: str, value: dict, verifier) -> None:
        changed = resign(value, field)
        with patch.dict(M.FP, {key: changed[field]}):
            with self.assertRaises(ProofEngineError):
                verifier(changed)

    def test_valid_complete_stage(self) -> None:
        values = M.verify_all()
        self.assertEqual(
            values["progress"]["current_position"]["current_state"],
            "INTERNAL_NAMED_CANDIDATE_SELECTION_AND_CONTACT_PACKET_COMPLETE",
        )

    def test_summary_keeps_external_authority_closed(self) -> None:
        value = M.summary()
        self.assertEqual(value["rts_overall_planning_estimate_percent"], 80)
        self.assertEqual(value["product_readiness_score"], 93)
        self.assertEqual(value["selected_repository"], "jbexta/AgentPilot")
        self.assertEqual(value["pilot_participant_count"], 0)
        self.assertIsNone(value["named_recipient"])
        self.assertFalse(value["participant_contact_authorized"])
        self.assertFalse(value["external_actions_performed"])

    def test_prior_completion_change_fails_closed(self) -> None:
        prior = load(M.PATH["prior_completion"])
        prior["state"] = "CHANGED"
        prior = resign(prior, "completion_fingerprint")
        with patch.dict(M.PRIOR, {"completion": prior["completion_fingerprint"]}):
            with self.assertRaises(ProofEngineError):
                M.verify_prior_shortlist_history(completion=prior)

    def test_prior_status_change_fails_closed(self) -> None:
        prior = load(M.PATH["prior_status"])
        prior["current_position"]["next_gate"] = "CHANGED"
        prior = resign(prior, "map_fingerprint")
        with patch.dict(M.PRIOR, {"status": prior["map_fingerprint"]}):
            with self.assertRaises(ProofEngineError):
                M.verify_prior_shortlist_history(status=prior)

    def test_prior_checkpoint_external_action_fails_closed(self) -> None:
        prior = load(M.PATH["prior_checkpoint"])
        prior["participant_contact_performed"] = True
        prior = resign(prior, "checkpoint_fingerprint")
        with patch.dict(M.PRIOR, {"checkpoint": prior["checkpoint_fingerprint"]}):
            with self.assertRaises(ProofEngineError):
                M.verify_prior_shortlist_history(checkpoint=prior)

    def test_contract_raw_instruction_retention_fails_closed(self) -> None:
        value = copy.deepcopy(self.contract)
        value["source"]["raw_instruction_retained"] = True
        self.semantic_failure("contract", "contract_fingerprint", value, M.verify_contract)

    def test_contract_instruction_hash_drift_fails_closed(self) -> None:
        value = copy.deepcopy(self.contract)
        value["source"]["raw_instruction_sha256"] = "0" * 64
        self.semantic_failure("contract", "contract_fingerprint", value, M.verify_contract)

    def test_contract_outbound_message_authority_fails_closed(self) -> None:
        value = copy.deepcopy(self.contract)
        value["scope"]["outbound_message_limit"] = 1
        self.semantic_failure("contract", "contract_fingerprint", value, M.verify_contract)

    def test_contract_follow_up_authority_fails_closed(self) -> None:
        value = copy.deepcopy(self.contract)
        value["scope"]["follow_up_limit"] = 1
        self.semantic_failure("contract", "contract_fingerprint", value, M.verify_contract)

    def test_contract_public_issue_contact_fails_closed(self) -> None:
        value = copy.deepcopy(self.contract)
        value["scope"]["public_issue_or_pull_request_contact_allowed"] = True
        self.semantic_failure("contract", "contract_fingerprint", value, M.verify_contract)

    def test_contract_readiness_inflation_fails_closed(self) -> None:
        value = copy.deepcopy(self.contract)
        value["acceptance"]["product_readiness_score_required"] = 94
        self.semantic_failure("contract", "contract_fingerprint", value, M.verify_contract)

    def test_external_authority_widening_fails_closed(self) -> None:
        value = copy.deepcopy(self.contract)
        value["authority"]["participant_contact_authorized"] = True
        self.semantic_failure("contract", "contract_fingerprint", value, M.verify_contract)

    def test_selection_repository_change_fails_closed(self) -> None:
        value = copy.deepcopy(self.selection)
        value["selected_repository"] = "tmseidel/ai-git-bot"
        self.semantic_failure("selection", "selection_fingerprint", value, M.verify_selection)

    def test_selection_count_increase_fails_closed(self) -> None:
        value = copy.deepcopy(self.selection)
        value["selected_contact_candidate_count"] = 2
        self.semantic_failure("selection", "selection_fingerprint", value, M.verify_selection)

    def test_selection_silent_participant_fails_closed(self) -> None:
        value = copy.deepcopy(self.selection)
        value["pilot_participant_count"] = 1
        value["pilot_participant_selected"] = True
        self.semantic_failure("selection", "selection_fingerprint", value, M.verify_selection)

    def test_selection_pending_gate_deletion_fails_closed(self) -> None:
        value = copy.deepcopy(self.selection)
        value["pending_human_gates"].pop()
        self.semantic_failure("selection", "selection_fingerprint", value, M.verify_selection)

    def test_route_identity_false_verification_fails_closed(self) -> None:
        value = copy.deepcopy(self.route)
        value["observed_routes"][0]["identity_verification_status"] = "VERIFIED"
        self.semantic_failure("route", "route_review_fingerprint", value, M.verify_route)

    def test_route_acceptability_false_verification_fails_closed(self) -> None:
        value = copy.deepcopy(self.route)
        value["observed_routes"][0]["acceptability_status"] = "VERIFIED"
        self.semantic_failure("route", "route_review_fingerprint", value, M.verify_route)

    def test_route_recipient_population_fails_closed(self) -> None:
        value = copy.deepcopy(self.route)
        value["preferred_route"]["recipient_account"] = "AgentPilotAI"
        value["send_target_populated"] = True
        self.semantic_failure("route", "route_review_fingerprint", value, M.verify_route)

    def test_route_public_issue_guard_deletion_fails_closed(self) -> None:
        value = copy.deepcopy(self.route)
        value["prohibited_routes"].remove("PUBLIC_GITHUB_ISSUE_WITHOUT_EXPLICIT_INVITATION")
        self.semantic_failure("route", "route_review_fingerprint", value, M.verify_route)

    def test_message_recipient_population_fails_closed(self) -> None:
        value = copy.deepcopy(self.message)
        value["named_recipient"] = "AgentPilotAI"
        self.semantic_failure("message", "message_fingerprint", value, M.verify_message)

    def test_message_sent_state_fails_closed(self) -> None:
        value = copy.deepcopy(self.message)
        value["send_status"] = "SENT"
        value["send_event_count"] = 1
        self.semantic_failure("message", "message_fingerprint", value, M.verify_message)

    def test_message_reply_guard_deletion_fails_closed(self) -> None:
        value = copy.deepcopy(self.message)
        value["disclosures"].remove("reply is not consent and does not start analysis")
        self.semantic_failure("message", "message_fingerprint", value, M.verify_message)

    def test_message_body_disclosure_deletion_fails_closed(self) -> None:
        value = copy.deepcopy(self.message)
        value["body"] = value["body"].replace("No analysis would begin", "Analysis may begin")
        self.semantic_failure("message", "message_fingerprint", value, M.verify_message)

    def test_preflight_partial_pass_fails_closed(self) -> None:
        value = copy.deepcopy(self.preflight)
        value["partial_pass_allowed"] = True
        self.semantic_failure("preflight", "preflight_fingerprint", value, M.verify_preflight)

    def test_preflight_silent_completion_fails_closed(self) -> None:
        value = copy.deepcopy(self.preflight)
        value["checks"][0]["status"] = "PASS"
        value["completed_check_count"] = 1
        self.semantic_failure("preflight", "preflight_fingerprint", value, M.verify_preflight)

    def test_preflight_send_limit_fails_closed(self) -> None:
        value = copy.deepcopy(self.preflight)
        value["outbound_message_limit"] = 1
        self.semantic_failure("preflight", "preflight_fingerprint", value, M.verify_preflight)

    def test_response_positive_interest_as_consent_fails_closed(self) -> None:
        value = copy.deepcopy(self.response)
        value["response_classes"][0]["creates_consent"] = True
        self.semantic_failure("response", "response_protocol_fingerprint", value, M.verify_response)

    def test_response_follow_up_fails_closed(self) -> None:
        value = copy.deepcopy(self.response)
        value["no_response_policy"]["follow_up_count"] = 1
        self.semantic_failure("response", "response_protocol_fingerprint", value, M.verify_response)

    def test_response_ambiguous_intake_fails_closed(self) -> None:
        value = copy.deepcopy(self.response)
        value["response_classes"][2]["action"] = "START_INTAKE"
        self.semantic_failure("response", "response_protocol_fingerprint", value, M.verify_response)

    def test_response_raw_secret_retention_fails_closed(self) -> None:
        value = copy.deepcopy(self.response)
        value["raw_prohibited_payload_retention"] = True
        self.semantic_failure("response", "response_protocol_fingerprint", value, M.verify_response)

    def test_score_inflation_fails_closed(self) -> None:
        value = copy.deepcopy(self.score_hold)
        value["current_score"] = 94
        value["score_change"] = 1
        self.semantic_failure("score_hold", "score_hold_fingerprint", value, M.verify_score_hold)

    def test_completion_criterion_deletion_fails_closed(self) -> None:
        value = copy.deepcopy(self.completion)
        value["acceptance_results"].pop()
        self.semantic_failure("completion", "completion_fingerprint", value, M.verify_completion)

    def test_completion_send_event_fails_closed(self) -> None:
        value = copy.deepcopy(self.completion)
        value["message_send_event_count"] = 1
        self.semantic_failure("completion", "completion_fingerprint", value, M.verify_completion)

    def test_progress_inflation_fails_closed(self) -> None:
        value = copy.deepcopy(self.status)
        value["current_position"]["rts_overall_planning_estimate_percent"] = 81
        self.semantic_failure("status", "map_fingerprint", value, M.verify_progress)

    def test_progress_contact_authority_fails_closed(self) -> None:
        value = copy.deepcopy(self.status)
        value["current_position"]["participant_contact_authorized"] = True
        self.semantic_failure("status", "map_fingerprint", value, M.verify_progress)

    def test_checkpoint_send_action_fails_closed(self) -> None:
        value = copy.deepcopy(self.checkpoint)
        value["message_send_performed"] = True
        self.semantic_failure("checkpoint", "checkpoint_fingerprint", value, M.verify_checkpoint)

    def test_checkpoint_participant_count_fails_closed(self) -> None:
        value = copy.deepcopy(self.checkpoint)
        value["pilot_participant_count"] = 1
        self.semantic_failure("checkpoint", "checkpoint_fingerprint", value, M.verify_checkpoint)

    def test_verifier_is_read_only(self) -> None:
        with patch.object(Path, "write_text", side_effect=AssertionError("write attempted")):
            M.verify_all()


if __name__ == "__main__":
    unittest.main()
