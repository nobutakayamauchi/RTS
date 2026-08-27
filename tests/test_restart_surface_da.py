import tempfile, unittest
from pathlib import Path
from restart_surface import RestartValidationError, build_surface, restart_equivalence, validate_surface, git_blob_sha_bytes

class RestartSurfaceDA(unittest.TestCase):
    def state(self):
        return {'goal':'g','repo':'r','branch':'b','commit':'abcdef123','changed':['x'],'verified':['y'],'unresolved':['UNKNOWN: deployment identity'],'rollback':'revert B only','do_not_touch':['Child A'],'next_authorized_action':'verify'}
    def test_do_not_touch_cannot_be_lost(self):
        s=build_surface(Path('.'),self.state(),[]); self.assertEqual(s['do_not_touch'],['Child A'])
    def test_unknown_cannot_be_erased(self):
        s=build_surface(Path('.'),self.state(),[]); self.assertIn('UNKNOWN:',s['unresolved'][0])
    def test_overbudget_fails_instead_of_truncating(self):
        x=self.state(); x['unresolved']=['UNKNOWN:'+('z'*5000),'SECOND BLOCKER']
        with self.assertRaises(RestartValidationError): build_surface(Path('.'),x,[],max_active_chars=500)
    def test_restart_equivalence_detects_required_loss(self):
        s=build_surface(Path('.'),self.state(),[]); s['do_not_touch']=[]; q=restart_equivalence(self.state(),s); self.assertFalse(q['equivalent']); self.assertIn('do_not_touch',q['changed'])
    def test_inline_full_history_is_rejected(self):
        s=build_surface(Path('.'),self.state(),[]); s['full_history']='too much'
        with self.assertRaises(RestartValidationError): validate_surface(Path('.'),s)
