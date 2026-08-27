import json,tempfile,unittest
from pathlib import Path
from intelligence_compiler import CompilerValidationError,ingest_raw,initialize_job,load_manifest,process_next,verify_job,plan_full_recompile

class CompilerDA(unittest.TestCase):
    def record(self): return {'task_id':'t','main_work_completed':True,'outcome':'done','evidence_refs':['e'],'observations':[{'observation_id':'a','text':'A'},{'observation_id':'b','text':'B'}]}
    def setup(self,r,max_retries=2): raw=ingest_raw(r,self.record()); initialize_job(r,raw['raw_id'],1,max_retries); return raw['raw_id']
    def test_later_failure_does_not_erase_success(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); job=self.setup(r); process_next(r,job,lambda xs:{'ok':'a'}); first=load_manifest(r,job)['chunks'][0].copy(); process_next(r,job,lambda xs:(_ for _ in ()).throw(RuntimeError('poison'))); after=load_manifest(r,job)['chunks'][0]; self.assertEqual(after['status'],'COMPLETED'); self.assertEqual(after['result_fingerprint'],first['result_fingerprint']); self.assertTrue((r/after['result_path']).is_file())
    def test_learning_failure_never_invalidates_main_work(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); job=self.setup(r,1); process_next(r,job,lambda xs:(_ for _ in ()).throw(RuntimeError('poison'))); m=load_manifest(r,job); self.assertTrue(m['main_work_completed']); self.assertEqual(m['chunks'][0]['status'],'QUARANTINED')
    def test_retry_then_quarantine_is_chunk_local(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); job=self.setup(r,2); process_next(r,job,lambda xs:{'ok':True}); fail=lambda xs:(_ for _ in ()).throw(RuntimeError('x')); a=process_next(r,job,fail); b=process_next(r,job,fail); m=load_manifest(r,job); self.assertEqual(a['status'],'PENDING'); self.assertEqual(b['status'],'QUARANTINED'); self.assertEqual(m['chunks'][0]['status'],'COMPLETED')
    def test_completed_chunk_is_not_reprocessed(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); job=self.setup(r); seen=[]; process_next(r,job,lambda xs:(seen.append(xs[0]['observation_id']) or {'ok':True})); process_next(r,job,lambda xs:(seen.append(xs[0]['observation_id']) or {'ok':True})); self.assertEqual(seen,['a','b'])
    def test_tampered_raw_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); job=self.setup(r); raw=next((r/'raw').glob('*.json')); x=json.loads(raw.read_text()); x['record']['outcome']='tampered'; raw.write_text(json.dumps(x));
            with self.assertRaises(CompilerValidationError): verify_job(r,job,allow_incomplete=True)
    def test_full_recompile_without_reason_is_rejected(self):
        with self.assertRaises(CompilerValidationError): plan_full_recompile('   ')
