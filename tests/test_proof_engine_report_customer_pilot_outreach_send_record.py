from __future__ import annotations

import copy
import unittest

from proof_engine_pilot import report_customer_pilot_outreach_send_record as m


class OutreachSendRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = m.load(m.CONTRACT_PATH)
        cls.event = m.load(m.EVENT_PATH)
        cls.privacy = m.load(m.PRIVACY_PATH)
        cls.window = m.load(m.WINDOW_PATH)
        cls.score = m.load(m.SCORE_PATH)
        cls.completion = m.load(m.COMPLETION_PATH)
        cls.position = m.load(m.POSITION_PATH)
        cls.checkpoint = m.load(m.CHECKPOINT_PATH)

    def resign(self, value, field):
        changed = copy.deepcopy(value)
        changed.pop(field, None)
        changed[field] = m.fingerprint(changed)
        return changed

    def assertRejected(self, fn, value):
        with self.assertRaises(m.OutreachRecordError):
            fn(value)

    def test_verify_all(self):
        self.assertEqual(m.verify_all()["message_send_event_count"], 1)

    def test_prior_history(self):
        self.assertEqual(
            m.verify_prior_history()["completion"]["completion_fingerprint"],
            "4b721f6dadcf318809de7a64950deb58e1e5a556414194606a30f5508e4a2d31",
        )

    def test_contract(self):
        self.assertEqual(m.verify_contract()["allowed_record"]["route"], "DISCORD_DM")

    def test_event(self):
        self.assertEqual(m.verify_event()["evidence"]["class"], "HUMAN_ATTESTED")

    def test_privacy(self):
        self.assertFalse(m.verify_privacy()["raw_private_payload_retained"])

    def test_window(self):
        self.assertEqual(m.verify_window()["follow_up_limit"], 0)

    def test_score(self):
        self.assertEqual(m.verify_score()["current_product_readiness_score"], 93)

    def test_completion(self):
        self.assertEqual(m.verify_completion()["rts_overall_planning_estimate_percent"], 81)

    def test_position(self):
        self.assertEqual(m.verify_position()["current_position"]["response_event_count"], 0)

    def test_checkpoint(self):
        self.assertTrue(m.verify_checkpoint()["message_send_performed"])

    def test_tamper_fingerprint(self):
        changed = copy.deepcopy(self.event)
        changed["send_event_count"] = 2
        self.assertRejected(m.verify_event, changed)

    def test_reject_second_send_even_resigned(self):
        changed = copy.deepcopy(self.event)
        changed["send_event_count"] = 2
        changed = self.resign(changed, "event_fingerprint")
        self.assertRejected(m.verify_event, changed)

    def test_reject_follow_up(self):
        changed = copy.deepcopy(self.event)
        changed["follow_up_event_count"] = 1
        changed = self.resign(changed, "event_fingerprint")
        self.assertRejected(m.verify_event, changed)

    def test_reject_response_manufacture(self):
        changed = copy.deepcopy(self.event)
        changed["response_event_count"] = 1
        changed = self.resign(changed, "event_fingerprint")
        self.assertRejected(m.verify_event, changed)

    def test_reject_response_status_manufacture(self):
        changed = copy.deepcopy(self.event)
        changed["response_status"] = "POSITIVE"
        changed = self.resign(changed, "event_fingerprint")
        self.assertRejected(m.verify_event, changed)

    def test_reject_exact_message_claim(self):
        changed = copy.deepcopy(self.event)
        changed["evidence"]["message_exactly_verified"] = True
        changed = self.resign(changed, "event_fingerprint")
        self.assertRejected(m.verify_event, changed)

    def test_reject_delivery_receipt_claim(self):
        changed = copy.deepcopy(self.event)
        changed["evidence"]["independent_delivery_receipt_available"] = True
        changed = self.resign(changed, "event_fingerprint")
        self.assertRejected(m.verify_event, changed)

    def test_reject_message_storage(self):
        changed = copy.deepcopy(self.event)
        changed["evidence"]["message_body_stored"] = True
        changed = self.resign(changed, "event_fingerprint")
        self.assertRejected(m.verify_event, changed)

    def test_reject_screenshot_storage(self):
        changed = copy.deepcopy(self.event)
        changed["evidence"]["screenshot_stored"] = True
        changed = self.resign(changed, "event_fingerprint")
        self.assertRejected(m.verify_event, changed)

    def test_reject_time_precision_invention(self):
        changed = copy.deepcopy(self.event)
        changed["event_time_local"] = "15:47:00"
        changed["event_time_precision"] = "SECOND"
        changed = self.resign(changed, "event_fingerprint")
        self.assertRejected(m.verify_event, changed)

    def test_reject_participant_selection(self):
        changed = copy.deepcopy(self.event)
        changed["pilot_participant_selected"] = True
        changed = self.resign(changed, "event_fingerprint")
        self.assertRejected(m.verify_event, changed)

    def test_reject_intake(self):
        changed = copy.deepcopy(self.event)
        changed["customer_intake_performed"] = True
        changed = self.resign(changed, "event_fingerprint")
        self.assertRejected(m.verify_event, changed)

    def test_reject_analysis(self):
        changed = copy.deepcopy(self.event)
        changed["analysis_performed"] = True
        changed = self.resign(changed, "event_fingerprint")
        self.assertRejected(m.verify_event, changed)

    def test_reject_private_payload_retention(self):
        changed = copy.deepcopy(self.privacy)
        changed["raw_private_payload_retained"] = True
        changed = self.resign(changed, "privacy_fingerprint")
        self.assertRejected(m.verify_privacy, changed)

    def test_reject_missing_privacy_exclusion(self):
        changed = copy.deepcopy(self.privacy)
        changed["excluded_fields"].remove("private message body")
        changed = self.resign(changed, "privacy_fingerprint")
        self.assertRejected(m.verify_privacy, changed)

    def test_reject_monitoring_claim(self):
        changed = copy.deepcopy(self.window)
        changed["discord_content_monitoring_available"] = True
        changed = self.resign(changed, "window_fingerprint")
        self.assertRejected(m.verify_window, changed)

    def test_reject_instant_detection_claim(self):
        changed = copy.deepcopy(self.window)
        changed["instant_reply_detection_available"] = True
        changed = self.resign(changed, "window_fingerprint")
        self.assertRejected(m.verify_window, changed)

    def test_reject_followup_authority(self):
        changed = copy.deepcopy(self.window)
        changed["follow_up_authorized"] = True
        changed = self.resign(changed, "window_fingerprint")
        self.assertRejected(m.verify_window, changed)

    def test_reject_wait_shortening(self):
        changed = copy.deepcopy(self.window)
        changed["duration_days"] = 3
        changed = self.resign(changed, "window_fingerprint")
        self.assertRejected(m.verify_window, changed)

    def test_reject_readiness_increase(self):
        changed = copy.deepcopy(self.score)
        changed["current_product_readiness_score"] = 94
        changed["score_change"] = 1
        changed = self.resign(changed, "score_hold_fingerprint")
        self.assertRejected(m.verify_score, changed)

    def test_reject_completion_response(self):
        changed = copy.deepcopy(self.completion)
        changed["response_event_count"] = 1
        changed = self.resign(changed, "completion_fingerprint")
        self.assertRejected(m.verify_completion, changed)

    def test_reject_completion_followup(self):
        changed = copy.deepcopy(self.completion)
        changed["follow_up_event_count"] = 1
        changed = self.resign(changed, "completion_fingerprint")
        self.assertRejected(m.verify_completion, changed)

    def test_reject_completion_authority(self):
        changed = copy.deepcopy(self.completion)
        changed["authority"]["follow_up_authorized"] = True
        changed = self.resign(changed, "completion_fingerprint")
        self.assertRejected(m.verify_completion, changed)

    def test_reject_position_inflation(self):
        changed = copy.deepcopy(self.position)
        changed["current_position"]["rts_overall_planning_estimate_percent"] = 82
        changed = self.resign(changed, "map_fingerprint")
        self.assertRejected(m.verify_position, changed)

    def test_reject_position_consent(self):
        changed = copy.deepcopy(self.position)
        changed["current_position"]["customer_intake_authorized"] = True
        changed = self.resign(changed, "map_fingerprint")
        self.assertRejected(m.verify_position, changed)

    def test_reject_checkpoint_analysis(self):
        changed = copy.deepcopy(self.checkpoint)
        changed["analysis_performed"] = True
        changed = self.resign(changed, "checkpoint_fingerprint")
        self.assertRejected(m.verify_checkpoint, changed)

    def test_reject_checkpoint_write(self):
        changed = copy.deepcopy(self.checkpoint)
        changed["source_or_target_repository_writes_performed"] = True
        changed = self.resign(changed, "checkpoint_fingerprint")
        self.assertRejected(m.verify_checkpoint, changed)


if __name__ == "__main__":
    unittest.main()
