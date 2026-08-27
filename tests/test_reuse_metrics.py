import json,unittest
from pathlib import Path
from reuse_metrics import MetricsValidationError,compute_report,validate_report

def event(i,m,state='MEASURED',n=None,d=None,v=None,unit='ratio'):
    return {'event_id':i,'metric':m,'measurement_state':state,'numerator':n,'denominator':d,'value':v,'unit':unit,'source_ref':'test'}
class ReuseMetricsTests(unittest.TestCase):
    def test_rate_aggregation_keeps_denominator(self):
        r=compute_report([event('1','decision_reuse_rate',n=3,d=4),event('2','decision_reuse_rate',n=1,d=2)])['rts_reuse_metrics']['decision_reuse_rate']; self.assertEqual(r['numerator'],4); self.assertEqual(r['denominator'],6); self.assertAlmostEqual(r['value'],4/6)
    def test_count_metrics_sum(self):
        xs=[event('1','knowledge_debt_count',v=2,unit='count'),event('2','knowledge_debt_count',v=3,unit='count')]; self.assertEqual(compute_report(xs)['rts_reuse_metrics']['knowledge_debt_count']['value'],5)
    def test_restart_load_unit_is_chars(self):
        r=compute_report([event('1','restart_surface_load',v=700,unit='chars')]); m=r['rts_reuse_metrics']['restart_surface_load']; self.assertEqual(m['unit'],'chars'); self.assertTrue(r['claim_boundaries']['restart_surface_load_is_chars_not_tokens_or_time'])
    def test_measured_wins_over_estimated_without_relabeling_estimate(self):
        xs=[event('1','failure_reuse_rate','ESTIMATED',n=8,d=10),event('2','failure_reuse_rate','MEASURED',n=1,d=2)]; m=compute_report(xs)['rts_reuse_metrics']['failure_reuse_rate']; self.assertEqual(m['measurement_state'],'MEASURED'); self.assertEqual(m['source_event_count'],1); self.assertEqual(m['value'],.5)
    def test_duplicate_event_fails(self):
        e=event('1','decision_reuse_rate',n=1,d=2)
        with self.assertRaises(MetricsValidationError): compute_report([e,e])
    def test_committed_report_valid(self): self.assertTrue(validate_report(json.loads(Path('metrics/reuse_report.json').read_text()))['valid'])
