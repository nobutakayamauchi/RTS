import unittest

import olt_event_ingest as ingest


class OLTEventIngestTests(unittest.TestCase):
    def event(
        self,
        timestamp,
        *,
        actor="HUMAN",
        project="RTS",
        event_type="action",
        evidence="fixture",
        **extra,
    ):
        return ingest.normalize_event({
            "timestamp": timestamp,
            "project": project,
            "actor_class": actor,
            "event_type": event_type,
            "evidence_ref": evidence,
            **extra,
        })

    def test_pre_kernel_source_anchor_reproduces_22_25_olu(self):
        # Exact confirmed-human timestamps from RTS_human_intervention_dataset_v0_1.xlsx.
        stamps = [
            "2026-02-16T15:16:14+09:00",
            "2026-02-16T15:17:31+09:00",
            "2026-02-16T15:19:33+09:00",
            "2026-02-16T15:31:27+09:00",
            "2026-02-16T15:37:41+09:00",
            "2026-02-16T15:40:28+09:00",
            "2026-02-16T15:43:23+09:00",
            "2026-02-16T15:47:40+09:00",
            "2026-02-18T20:13:45+09:00",
            "2026-02-18T20:23:27+09:00",
            "2026-02-18T20:23:51+09:00",
            "2026-02-18T20:30:11+09:00",
            "2026-02-18T20:33:16+09:00",
            "2026-02-18T20:38:06+09:00",
            "2026-02-18T20:51:08+09:00",
            "2026-02-18T20:59:06+09:00",
            "2026-02-18T21:01:01+09:00",
        ]
        result = ingest.aggregate_window([self.event(stamp) for stamp in stamps])
        self.assertEqual(result.human_events, 17)
        self.assertAlmostEqual(result.active_minutes, 78.7, places=6)
        self.assertAlmostEqual(result.load.E, 22.2466666667, places=6)
        self.assertEqual(result.sessions, 2)
        self.assertEqual(result.bursts, 4)
        self.assertAlmostEqual(result.resolved_coverage, 1.0)
        self.assertAlmostEqual(result.automation_ratio, 0.0)

    def test_materialized_post_kernel_sample_stays_3_7_5(self):
        rows = [
            self.event("2026-02-26T09:12:45+00:00", actor="UNKNOWN"),
            self.event("2026-02-26T09:16:30+00:00", actor="UNKNOWN"),
            self.event("2026-02-26T09:25:42+00:00", actor="UNKNOWN"),
            self.event("2026-02-26T10:10:32+00:00", actor="UNKNOWN"),
            self.event("2026-02-26T10:23:21+00:00", actor="UNKNOWN"),
            self.event("2026-02-26T14:24:29+00:00", actor="AUTO"),
            self.event("2026-02-26T14:25:17+00:00", actor="AUTO"),
            self.event("2026-02-26T14:30:53+00:00", actor="AUTO"),
            self.event("2026-02-26T14:34:31+00:00", actor="AUTO"),
            self.event("2026-02-26T14:39:47+00:00", actor="AUTO"),
            self.event("2026-02-26T14:40:43+00:00", actor="AUTO"),
            self.event("2026-02-27T01:23:22+00:00", actor="AUTO"),
            self.event("2026-02-27T22:16:48+00:00"),
            self.event("2026-02-27T22:24:47+00:00"),
            self.event("2026-02-27T22:27:33+00:00"),
        ]
        result = ingest.aggregate_window(rows)
        self.assertEqual((result.human_events, result.auto_events, result.unknown_events), (3, 7, 5))
        self.assertAlmostEqual(result.resolved_coverage, 10 / 15)
        self.assertAlmostEqual(result.automation_ratio, 0.7)
        self.assertAlmostEqual(result.active_minutes, 10.75, places=6)
        self.assertAlmostEqual(result.load.E, 3.7166666667, places=6)

    def test_auto_and_unknown_do_not_create_semantic_human_load(self):
        rows = [
            self.event("2026-08-11T20:00:00+09:00", actor="AUTO", project="A"),
            self.event("2026-08-11T20:01:00+09:00", actor="UNKNOWN", project="B"),
            self.event("2026-08-11T20:02:00+09:00", actor="HUMAN", project="A"),
            self.event("2026-08-11T20:03:00+09:00", actor="AUTO", project="C"),
            self.event("2026-08-11T20:04:00+09:00", actor="HUMAN", project="A"),
        ]
        result = ingest.aggregate_window(rows)
        self.assertEqual(result.load.J, 0)
        self.assertEqual(result.load.R, 0)
        self.assertEqual(result.load.X, 0)
        self.assertAlmostEqual(result.load.E, 2 + 2 / 15)

    def test_explicit_human_decision_rework_and_switch_are_counted(self):
        rows = [
            self.event(
                "2026-08-11T20:00:00+09:00",
                project="RTS",
                event_type="decision",
                decision_severity=2,
            ),
            self.event(
                "2026-08-11T20:05:00+09:00",
                project="Vlog",
                event_type="failure",
                rework_severity=3,
            ),
        ]
        result = ingest.aggregate_window(rows)
        self.assertEqual(result.load.J, 2)
        self.assertEqual(result.load.R, 3)
        self.assertEqual(result.load.X, 1)

    def test_governed_stage_is_deduplicated_and_conflict_fails_closed(self):
        rows = [
            self.event(
                "2026-08-11T20:00:00+09:00",
                governed_stage_id="goal-1",
                gate_elapsed_min=15,
            ),
            self.event(
                "2026-08-11T20:02:00+09:00",
                governed_stage_id="goal-1",
                gate_elapsed_min=15,
            ),
            self.event(
                "2026-08-11T20:04:00+09:00",
                governed_stage_id="goal-2",
                gate_elapsed_min=30,
            ),
        ]
        result = ingest.aggregate_window(rows)
        self.assertEqual(result.governed_stages, 2)
        self.assertEqual(result.gate_minutes, 45)
        self.assertEqual(result.load.O, 5)

        conflict = list(rows)
        conflict.append(self.event(
            "2026-08-11T20:06:00+09:00",
            governed_stage_id="goal-1",
            gate_elapsed_min=16,
        ))
        with self.assertRaises(ingest.OLTIngestError):
            ingest.aggregate_window(conflict)

    def test_unknown_cannot_be_promoted_to_decision_by_field_presence(self):
        with self.assertRaises(ingest.OLTIngestError):
            self.event(
                "2026-08-11T20:00:00+09:00",
                actor="UNKNOWN",
                event_type="decision",
                decision_severity=2,
            )

    def test_naive_timestamp_and_missing_evidence_fail_closed(self):
        with self.assertRaises(ingest.OLTIngestError):
            self.event("2026-08-11T20:00:00")
        with self.assertRaises(ingest.OLTIngestError):
            ingest.normalize_event({
                "timestamp": "2026-08-11T20:00:00+09:00",
                "project": "RTS",
                "actor_class": "HUMAN",
                "event_type": "action",
                "evidence_ref": "",
            })


if __name__ == "__main__":
    unittest.main()
