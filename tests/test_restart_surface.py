import json, tempfile, unittest
from pathlib import Path
from restart_surface import RestartValidationError, build_surface, validate_surface, restart_equivalence, decide_restart, git_blob_sha_bytes

class RestartSurfaceTests(unittest.TestCase):
    def state(self):
        return {'goal':'g','repo':'r','branch':'b','commit':'abcdef123','changed':['c'],'verified':['v'],'unresolved':['UNKNOWN: x'],'rollback':'rollback B','do_not_touch':['A'],'next_authorized_action':'verify'}
    def refs(self,root):
        p=root/'source.md'; p.write_text('source\n'); return [{'path':'source.md','git_blob_sha':git_blob_sha_bytes(p.read_bytes())}]
    def test_committed_surface_valid(self):
        s=json.loads(Path('restart/restart_surface.json').read_text()); self.assertTrue(validate_surface(Path('.'),s)['valid'])
    def test_fixed_denominator_equivalent(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); st=self.state(); s=build_surface(r,st,self.refs(r)); self.assertTrue(restart_equivalence(st,s)['equivalent'])
    def test_missing_required_field_fails(self):
        st=self.state(); del st['rollback']
        with self.assertRaises(RestartValidationError): build_surface(Path('.'),st,[])
    def test_stale_source_fails(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); st=self.state(); refs=self.refs(r); s=build_surface(r,st,refs); (r/'source.md').write_text('changed\n')
            with self.assertRaises(RestartValidationError): validate_surface(r,s)
    def test_path_escape_fails(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); outside=r.parent/'outside-restart.md'; outside.write_text('x')
            refs=[{'path':'../outside-restart.md','git_blob_sha':git_blob_sha_bytes(outside.read_bytes())}]
            try:
                with self.assertRaises(RestartValidationError): build_surface(r,self.state(),refs)
            finally: outside.unlink(missing_ok=True)
    def test_non_authority(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); s=build_surface(r,self.state(),self.refs(r)); self.assertEqual(s['execution_authority'],'NONE'); self.assertEqual(s['promotion_authority'],'NONE')
    def test_full_history_reopen_is_explicit(self):
        d=decide_restart({}, {'unresolved_blocker':True}); self.assertEqual(d['decision'],'REOPEN_FULL_HISTORY'); self.assertEqual(d['reason'],'UNRESOLVED_BLOCKER')
    def test_selective_recall_handoff_is_bounded(self):
        d=decide_restart({}, {'missing_detail':True,'scope_tags':['context']}); self.assertEqual(d['decision'],'SELECTIVE_RECALL'); self.assertEqual(d['recall_request']['max_results'],1)
    def test_continue_path_is_non_authorizing(self):
        d=decide_restart({}, {}); self.assertEqual(d['decision'],'CONTINUE_FROM_SURFACE'); self.assertEqual(d['execution_authority'],'NONE')
