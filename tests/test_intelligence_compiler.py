import json,tempfile,unittest
from pathlib import Path
from intelligence_compiler import CompilerValidationError,ingest_raw,initialize_job,load_manifest,process_next,verify_job,plan_differential_reevaluation,plan_full_recompile

class CompilerTests(unittest.TestCase):
    def record(self):
        return {'task_id':'t1','main_work_completed':True,'outcome':'done','evidence_refs':['e1'],'observations':[{'observation_id':'o1','text':'one'},{'observation_id':'o2','text':'two'},{'observation_id':'o3','text':'three'}]}
    def setup_job(self,root,chunk_size=1,max_retries=2):
        raw=ingest_raw(root,self.record()); initialize_job(root,raw['raw_id'],chunk_size,max_retries); return raw['raw_id']
    def test_raw_exists_before_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); raw=ingest_raw(r,self.record()); self.assertTrue(Path(raw['path']).is_file()); self.assertFalse((r/'jobs'/raw['raw_id']/'manifest.json').exists())
    def test_initialization_is_deterministic_and_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); raw=ingest_raw(r,self.record()); a=initialize_job(r,raw['raw_id'],2,2); b=initialize_job(r,raw['raw_id'],2,2); self.assertEqual(a,b); self.assertEqual(len(a['chunks']),2)
    def test_resume_processes_first_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); job=self.setup_job(r); process_next(r,job,lambda xs:{'candidate':xs[0]['observation_id']}); m=load_manifest(r,job); self.assertEqual(m['chunks'][0]['status'],'COMPLETED'); self.assertEqual(m['chunks'][1]['status'],'PENDING')
    def test_successful_job_verifies(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); job=self.setup_job(r,2); process_next(r,job,lambda xs:{'ids':[x['observation_id'] for x in xs]}); process_next(r,job,lambda xs:{'ids':[x['observation_id'] for x in xs]}); self.assertTrue(verify_job(r,job)['valid'])
    def test_processor_cannot_grant_authority(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); job=self.setup_job(r,3,1); out=process_next(r,job,lambda xs:{'promotion_authority':'APPROVED'}); self.assertEqual(out['status'],'QUARANTINED'); self.assertTrue(out['main_work_completed'])
    def test_differential_plan_only_returns_affected(self):
        p=plan_differential_reevaluation(['o2'],{'d1':['o1'],'d2':['o2','o3']}); self.assertEqual(p['affected_decision_ids'],['d2']); self.assertFalse(p['full_recompile'])
    def test_full_recompile_requires_reason(self):
        with self.assertRaises(CompilerValidationError): plan_full_recompile('')
        self.assertTrue(plan_full_recompile('schema changed')['full_recompile'])
    def test_committed_sample_verifies(self):
        stores=Path('intelligence/compiler_sample'); manifests=list(stores.glob('jobs/*/manifest.json')); self.assertEqual(len(manifests),1); self.assertTrue(verify_job(stores,manifests[0].parent.name)['valid'])
