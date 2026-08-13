import copy
import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import standalone_prototype, structural_prototype
from test_emergency_prototypes import base_case, valid_recovery
spec=importlib.util.spec_from_file_location('lifecycle',ROOT/'thin-rts'/'ultimate-loop'/'lifecycle.py')
lifecycle=importlib.util.module_from_spec(spec); spec.loader.exec_module(lifecycle)
AT=datetime(2026,8,13,19,7,tzinfo=timezone.utc)
def v(_): return {'state':'DEPLOYMENT_VALIDATED','stable_eligible':True,'post_deployment_binding':['o','e','s'],'validated_candidate_id':'fallback-b','validated_at':'2026-08-14T04:06:30+09:00'}
def s(c): return structural_prototype.evaluate(c,AT,lifecycle_evaluator=lifecycle.evaluate,recovery_validator=v)
def n(c): return standalone_prototype.evaluate(c,AT,recovery_validator=v)
class ReviewRegressions(unittest.TestCase):
 def test_newer_sample(self):
  c=base_case(); c['emergency']['recovery']=valid_recovery(); c['emergency']['health']['observed_at']='2026-08-14T04:07:00+09:00'
  self.assertEqual(s(copy.deepcopy(c))['state'],'TEMPORARY_RECOVERY_VALIDATED'); self.assertEqual(n(copy.deepcopy(c))['state'],'TEMPORARY_RECOVERY_VALIDATED')
 def test_healthy_does_not_erase_recovery(self):
  c=base_case(); c['emergency']['recovery']=valid_recovery(); c['emergency']['health']['state']='HEALTHY'; c['emergency']['health']['observed_at']='2026-08-14T04:07:00+09:00'
  for r in (s(copy.deepcopy(c)),n(copy.deepcopy(c))): self.assertEqual(r['state'],'TEMPORARY_RECOVERY_VALIDATED'); self.assertFalse(r['automatic_failback_authorized'])
 def test_trigger_snapshot_required(self):
  c=base_case(); c['emergency']['recovery']=valid_recovery(); del c['emergency']['recovery']['trigger_observed_at']
  with self.assertRaises(ValueError): s(copy.deepcopy(c))
  with self.assertRaises(ValueError): n(copy.deepcopy(c))
 def test_mode_enum(self):
  c=base_case(); c['emergency']['policy']['operation_mode']='READ_WRITE_SINGLE_WRTER'
  with self.assertRaises(ValueError): s(copy.deepcopy(c))
  with self.assertRaises(ValueError): n(copy.deepcopy(c))
if __name__=='__main__': unittest.main()
