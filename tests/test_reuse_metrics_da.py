import unittest
from reuse_metrics import compute_report

def e(i,m,state='MEASURED',n=None,d=None,v=None,unit='ratio'):
    return {'event_id':i,'metric':m,'measurement_state':state,'numerator':n,'denominator':d,'value':v,'unit':unit,'source_ref':'da'}
class ReuseMetricsDA(unittest.TestCase):
    def test_provider_cache_cannot_populate_decision_reuse(self):
        r=compute_report([e('p','cached_input_ratio',n=90,d=100)]); self.assertEqual(r['provider_cache']['cached_input_ratio']['value'],.9); d=r['rts_reuse_metrics']['decision_reuse_rate']; self.assertEqual(d['measurement_state'],'UNKNOWN'); self.assertIsNone(d['value'])
    def test_missing_is_unknown_not_zero(self):
        m=compute_report([])['rts_reuse_metrics']['human_intervention_count']; self.assertEqual(m['measurement_state'],'UNKNOWN'); self.assertIsNone(m['value'])
    def test_estimated_never_becomes_measured(self):
        m=compute_report([e('1','decision_reuse_rate','ESTIMATED',n=7,d=10)])['rts_reuse_metrics']['decision_reuse_rate']; self.assertEqual(m['measurement_state'],'ESTIMATED'); self.assertEqual(m['value'],.7)
    def test_zero_denominator_is_unknown(self):
        m=compute_report([e('1','retrieval_precision',n=0,d=0)])['rts_reuse_metrics']['retrieval_precision']; self.assertEqual(m['measurement_state'],'UNKNOWN'); self.assertIsNone(m['value']); self.assertEqual(m['reason'],'ZERO_DENOMINATOR')
    def test_provider_namespace_does_not_contain_decision_reuse(self): self.assertNotIn('decision_reuse_rate',compute_report([])['provider_cache'])
    def test_metrics_cannot_authorize_behavior(self):
        r=compute_report([]); self.assertEqual((r['execution_authority'],r['optimization_authority'],r['promotion_authority']),('NONE','NONE','NONE'))
