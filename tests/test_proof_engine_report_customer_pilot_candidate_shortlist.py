from __future__ import annotations

import copy
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from proof_engine_pilot.core import ProofEngineError, fingerprint, load
from proof_engine_pilot import report_customer_pilot_candidate_shortlist as m


@contextmanager
def resigned(key: str, value: dict, field: str):
    material = copy.deepcopy(value)
    material.pop(field, None)
    signed = fingerprint(material)
    value[field] = signed
    with patch.dict(m.FP, {key: signed}):
        yield value


class CandidateShortlistTests(unittest.TestCase):
    def test_01_complete_stage(self):
        value = m.verify_candidate_shortlist_stage()
        self.assertEqual(value["summary"]["recommended_candidate_repository"], "jbexta/AgentPilot")
        self.assertFalse(value["summary"]["participant_contact_authorized"])

    def test_02_contract(self):
        self.assertEqual(m.verify_contract()["acceptance"]["candidate_count"], 3)

    def test_03_universe(self):
        self.assertEqual(m.verify_universe()["candidate_count"], 3)

    def test_04_evidence(self):
        self.assertEqual(m.verify_evidence()["evidence_item_count"], 12)

    def test_05_scores(self):
        self.assertEqual(m.verify_scores()["ranking"][0], "CAND-001")

    def test_06_decision(self):
        self.assertIsNone(m.verify_decision()["selected_candidate"])

    def test_07_risk(self):
        self.assertEqual(m.verify_risk()["contact_event_count"], 0)

    def test_08_score_hold(self):
        self.assertEqual(m.verify_score_hold()["product_readiness_score_after"], 93)

    def test_09_completion(self):
        self.assertEqual(m.verify_completion()["selected_count"], 0)

    def test_10_progress(self):
        self.assertEqual(m.verify_progress()["current_position"]["rts_overall_planning_estimate_percent"], 79)

    def test_11_checkpoint(self):
        self.assertFalse(m.verify_checkpoint()["participant_contact_performed"])

    def test_12_contract_fingerprint_tamper(self):
        value = load(m.PATH["contract"])
        value["objective"] += " changed"
        with self.assertRaises(ProofEngineError):
            m.verify_contract(value)

    def test_13_contract_named_selection_not_authorized(self):
        value = load(m.PATH["contract"])
        value["authorized_now"]["named_candidate_selection"] = True
        with resigned("contract", value, "contract_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "authorization contract"):
                m.verify_contract(value)

    def test_14_contract_contact_not_authorized(self):
        value = load(m.PATH["contract"])
        value["authority"]["participant_contact_authorized"] = True
        with resigned("contract", value, "contract_fingerprint"):
            with self.assertRaises(ProofEngineError):
                m.verify_contract(value)

    def test_15_universe_private_repo_rejected(self):
        value = load(m.PATH["universe"])
        value["candidate_records"][0]["visibility"] = "private"
        record = value["candidate_records"][0]
        material = {k: v for k, v in record.items() if k != "candidate_fingerprint"}
        record["candidate_fingerprint"] = fingerprint(material)
        with resigned("universe", value, "universe_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "public individual"):
                m.verify_universe(value)

    def test_16_universe_candidate_addition_rejected(self):
        value = load(m.PATH["universe"])
        value["candidate_records"].append(copy.deepcopy(value["candidate_records"][0]))
        value["candidate_count"] = 4
        with resigned("universe", value, "universe_fingerprint"):
            with self.assertRaises(ProofEngineError):
                m.verify_universe(value)

    def test_17_evidence_withheld_conclusion_rejected(self):
        value = load(m.PATH["evidence"])
        value["records"][0]["withheld_conclusions"].pop()
        with resigned("evidence", value, "snapshot_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "withheld"):
                m.verify_evidence(value)

    def test_18_scores_threshold_lowering_rejected(self):
        value = load(m.PATH["scores"])
        value["minimum_public_score"] = 70
        with resigned("scores", value, "scores_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "threshold"):
                m.verify_scores(value)

    def test_19_scores_ranking_change_rejected(self):
        value = load(m.PATH["scores"])
        value["ranking"] = ["CAND-002", "CAND-001", "CAND-003"]
        with resigned("scores", value, "scores_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "ranking"):
                m.verify_scores(value)

    def test_20_scores_selection_rejected(self):
        value = load(m.PATH["scores"])
        value["selected_candidate_id"] = "CAND-001"
        with resigned("scores", value, "scores_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "selection"):
                m.verify_scores(value)

    def test_21_scores_sum_mismatch_rejected(self):
        value = load(m.PATH["scores"])
        value["score_records"][0]["criterion_scores"][0]["score"] = 13
        record = value["score_records"][0]
        material = {k: v for k, v in record.items() if k != "score_fingerprint"}
        record["score_fingerprint"] = fingerprint(material)
        with resigned("scores", value, "scores_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "score sum"):
                m.verify_scores(value)

    def test_22_decision_selected_candidate_rejected(self):
        value = load(m.PATH["decision"])
        value["selected_candidate"] = {"candidate_id": "CAND-001"}
        with resigned("decision", value, "decision_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "contact target"):
                m.verify_decision(value)

    def test_23_decision_contact_channel_rejected(self):
        value = load(m.PATH["decision"])
        value["contact_channel"] = "PUBLIC_ISSUE"
        with resigned("decision", value, "decision_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "contact target"):
                m.verify_decision(value)

    def test_24_risk_contact_status_rejected(self):
        value = load(m.PATH["risk"])
        value["contact_status"] = "AUTHORIZED"
        with resigned("risk", value, "risk_review_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "contact already"):
                m.verify_risk(value)

    def test_25_risk_prohibited_actions_weakened(self):
        value = load(m.PATH["risk"])
        value["prohibited_actions"].pop()
        with resigned("risk", value, "risk_review_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "prohibited"):
                m.verify_risk(value)

    def test_26_readiness_score_increase_rejected(self):
        value = load(m.PATH["score_hold"])
        value["product_readiness_score_after"] = 94
        value["score_change"] = 1
        with resigned("score_hold", value, "score_hold_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "score changed"):
                m.verify_score_hold(value)

    def test_27_completion_selected_count_rejected(self):
        value = load(m.PATH["completion"])
        value["selected_count"] = 1
        with resigned("completion", value, "completion_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "count"):
                m.verify_completion(value)

    def test_28_progress_contact_authority_rejected(self):
        value = load(m.PATH["status"])
        value["current_position"]["participant_contact_authorized"] = True
        with resigned("status", value, "map_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "widened"):
                m.verify_progress(value)

    def test_29_checkpoint_external_action_rejected(self):
        value = load(m.PATH["checkpoint"])
        value["participant_contact_performed"] = True
        with resigned("checkpoint", value, "checkpoint_fingerprint"):
            with self.assertRaisesRegex(ProofEngineError, "external action"):
                m.verify_checkpoint(value)


if __name__ == "__main__":
    unittest.main()
