from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path('.')
ITEM = 'RTS-FRZ-000013'
BRANCH = 'feature/frz-000013-incremental-resumable-intelligence-compiler-v1'


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    print('+', ' '.join(args), flush=True)
    return subprocess.run(args, text=True, check=check)


def write(path: str, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')


def write_json(path: str, value: object) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n')


def current(item_id: str) -> dict:
    pointer = json.loads((ROOT / 'freezer/items' / item_id / 'current.json').read_text())
    return json.loads((ROOT / pointer['path']).read_text())


def assert_start() -> None:
    assert current('RTS-FRZ-000011')['status'] == 'COMPLETED'
    assert current('RTS-FRZ-000012')['status'] == 'COMPLETED'
    c = current(ITEM)
    assert c['version'] == 1 and c['status'] == 'FROZEN' and c['build_authority'] == 'NOT_APPROVED', c
    for i in ('RTS-FRZ-000014', 'RTS-FRZ-000015'):
        x = current(i)
        assert x['status'] == 'FROZEN' and x['build_authority'] == 'NOT_APPROVED', x
    active = []
    for p in (ROOT / 'freezer/items').glob('RTS-FRZ-*/current.json'):
        x = current(p.parent.name)
        if x['status'] == 'IN_PROGRESS':
            active.append(x['item_id'])
    assert active == [], active
    run('python', '-m', 'freezer.cli', 'verify')
    run('python', '-m', 'freezer.build_assessment', 'verify')


def materialize_governance() -> None:
    base = 'docs/implementation/frz000013_inputs'
    assessment = {
        'assessor': 'RTS governed build assessment — Child C incremental resumable intelligence compiler',
        'rationale': 'Child C is bounded to repository-local raw-first learning compilation. Completed task outcome/evidence is persisted before compilation; observations are chunked deterministically; successful chunks checkpoint independently; failed chunks retry then quarantine without invalidating completed main work; differential reevaluation is explicit and proposal-only.',
        'expected_effect': {'impact': 5, 'strategic_fit': 5, 'revenue_leverage': 4, 'risk_reduction': 5, 'recurrence': 5, 'confidence': 4},
        'implementation': {'from_scratch_hours': 18, 'integration_hours': 3, 'validation_hours': 4, 'unknown_buffer_hours': 2},
        'github_scan': {
            'performed': True,
            'repositories': ['nobutakayamauchi/RTS'],
            'queries': ['outcome learning checkpoints resume quarantine idempotency', 'selective recall lifecycle provenance', 'restart surface raw evidence'],
            'assets': [
                {'repository': 'nobutakayamauchi/RTS', 'path': 'selective_recall/', 'ref': '825d2a2b398ab128fed7c3f8920393de0e75999d', 'kind': 'code', 'reuse_mode': 'ADAPT', 'license_status': 'OWNED', 'estimated_hours_saved': 3, 'notes': 'Reuse provenance, fail-closed validation, lifecycle non-authority.'},
                {'repository': 'nobutakayamauchi/RTS', 'path': 'restart_surface/', 'ref': '825d2a2b398ab128fed7c3f8920393de0e75999d', 'kind': 'code', 'reuse_mode': 'ADAPT', 'license_status': 'OWNED', 'estimated_hours_saved': 3, 'notes': 'Reuse deterministic bounded state, source identity, restart-safe semantics.'},
                {'repository': 'nobutakayamauchi/RTS', 'path': 'freezer/', 'ref': '825d2a2b398ab128fed7c3f8920393de0e75999d', 'kind': 'code', 'reuse_mode': 'REFERENCE', 'license_status': 'OWNED', 'estimated_hours_saved': 2, 'notes': 'Reuse append-only governance, WIP=1, assessment/preflight and verification.'},
            ],
            'gaps': ['No repository-local compiler currently guarantees raw-first persistence plus independent chunk checkpoints.', 'No current learning loop proves successful chunks survive later failure/quarantine.'],
        },
        'risks': ['Learning failure could incorrectly roll back completed task state.', 'Retry could recompute successful chunks.', 'A poison chunk could block the entire queue.', 'Full-corpus reevaluation could become the accidental default.', 'Proposal output could be mistaken for applied promotion.'],
    }
    preflight = {
        'outcome': 'PASS',
        'assessor': 'RTS implementation preflight — Child C incremental resumable intelligence compiler',
        'rationale': 'Repository-local compiler with explicit raw ingest, deterministic chunk manifest, per-chunk result checkpoint, first-incomplete resume, bounded retry/quarantine, idempotency keys, differential reevaluation and proposal-only authority. Main task completion is immutable from learning failures.',
        'affected_boundaries': ['new intelligence_compiler package', 'deterministic compiler sample store', 'focused compiler and destructive tests', 'RTS-FRZ-000013 lifecycle records'],
        'existing_assumptions': ['Child A and B are COMPLETED.', 'Completed main work is authoritative input and learning is downstream.', 'Raw outcome/evidence can be fingerprinted deterministically.', 'Promotion/application remains governed elsewhere.'],
        'data_migration': {'required': False, 'notes': 'No existing memory/history store is rewritten.'},
        'external_interfaces': ['repository-local Python API/CLI only', 'no provider/network/deployment/action surface'],
        'approval_changes': ['compiler output application_authority=NONE', 'promotion_authority=NONE', 'only RTS-FRZ-000013 may enter WIP'],
        'public_documents': ['intelligence_compiler/README.md', 'thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000013_2026-08-27.md'],
        'regression_tests': ['raw-first persistence', 'deterministic chunking', 'resume first incomplete', 'successful checkpoint preservation', 'retry/quarantine isolation', 'idempotent replay', 'raw/result fingerprint verification', 'differential reevaluation', 'explicit full-recompile reason', 'non-authority', 'A/B and FREEZER regressions'],
        'hidden_dependencies': ['filesystem atomic replace semantics', 'stable JSON canonicalization', 'FREEZER WIP=1', 'completed task outcome/evidence identity'],
        'rollback_boundary': 'Revert Child C package/sample/tests/docs/lifecycle only; preserve completed A/B and raw source outcomes.',
        'completion_conditions': ['Raw record exists before any job manifest.', 'Successful chunks survive later failures.', 'First incomplete chunk resumes without recomputing completed chunks.', 'Failed chunk retries then quarantines independently.', 'Learning failure never flips completed main work.', 'Full-corpus reevaluation requires an explicit reason.', 'All compiler/A/B/FREEZER tests pass.', 'C reaches COMPLETED while D-E remain FROZEN/NOT_APPROVED.'],
        'decomposition': {'required': False, 'child_candidates': []},
        'risks': ['Crash can occur between result write and manifest update; recovery must adopt a valid orphan result.', 'Processor output must remain proposal-only.', 'Changing compiler_version changes idempotency identity.'],
    }
    write_json(f'{base}/build_assessment_input.json', assessment)
    write_json(f'{base}/preflight_input.json', preflight)
    write_json(f'{base}/approve_selected.json', {'build_authority': 'APPROVED', 'status': 'SELECTED'})
    write_json(f'{base}/start_in_progress.json', {'status': 'IN_PROGRESS'})
    write('docs/implementation/FRZ_000013_INCREMENTAL_RESUMABLE_INTELLIGENCE_COMPILER_V1_TASK.md', '''# FRZ-000013 — Incremental / Resumable Intelligence Compiler v1

Raw completed-task outcome/evidence is durable before learning starts. Compilation is deterministic, chunked, checkpointed, resumable and proposal-only. A failed chunk may retry/quarantine; it may not erase successful chunks or invalidate completed main work. Full-corpus reevaluation requires an explicit reason.
''')


def govern_to_wip() -> None:
    b = 'docs/implementation/frz000013_inputs'
    run('python', '-m', 'freezer.build_assessment', 'create', ITEM, '--input', f'{b}/build_assessment_input.json')
    out = subprocess.check_output(['python', '-m', 'freezer.build_assessment', 'gate', ITEM], text=True)
    g = json.loads(out)
    assert g['recommendation'] == 'BUILD_NOW' and g['assessment_state'] == 'CURRENT' and not g['selection_ready'], g
    run('python', '-m', 'freezer.preflight', 'create', ITEM, '--input', f'{b}/preflight_input.json')
    run('python', '-m', 'freezer.cli', 'revise', ITEM, '--input', f'{b}/approve_selected.json')
    g = json.loads(subprocess.check_output(['python', '-m', 'freezer.build_assessment', 'gate', ITEM], text=True))
    assert g['preflight_state'] == 'PASS' and g['recommendation'] == 'BUILD_NOW' and g['selection_ready'] is True, g
    run('python', '-m', 'freezer.cli', 'revise', ITEM, '--input', f'{b}/start_in_progress.json')
    run('python', '-m', 'freezer.cli', 'reindex')
    run('python', '-m', 'freezer.build_assessment', 'reindex')
    run('python', '-m', 'freezer.cli', 'verify')
    run('python', '-m', 'freezer.build_assessment', 'verify')
    active = [p.parent.name for p in (ROOT / 'freezer/items').glob('RTS-FRZ-*/current.json') if current(p.parent.name)['status'] == 'IN_PROGRESS']
    assert active == [ITEM], active


def prove_initial_death() -> None:
    Path('intelligence_compiler').mkdir(exist_ok=True)
    write('intelligence_compiler/__init__.py', 'from .core import *\n')
    write('intelligence_compiler/core.py', '''from __future__ import annotations
import json
from pathlib import Path

def ingest_raw(root, record):
    root=Path(root); (root/'raw').mkdir(parents=True,exist_ok=True); p=root/'raw'/'raw.json'; p.write_text(json.dumps(record)); return {'raw_id':'raw','path':str(p)}

def initialize_job(root, raw_id, chunk_size=1, max_retries=2):
    root=Path(root); obs=json.loads((root/'raw'/'raw.json').read_text())['observations']; m={'main_work_completed':True,'chunks':[{'index':i,'status':'PENDING','value':x} for i,x in enumerate(obs)]}; (root/'manifest.json').write_text(json.dumps(m)); return m

def process_next(root, raw_id, processor):
    root=Path(root); p=root/'manifest.json'; m=json.loads(p.read_text()); c=next((x for x in m['chunks'] if x['status']=='PENDING'),None)
    if c is None: return m
    try:
        processor(c['value']); c['status']='COMPLETED'
    except Exception:
        for x in m['chunks']: x['status']='PENDING'
        m['main_work_completed']=False
    p.write_text(json.dumps(m)); return m
''')
    tmp = Path('tests/_frz000013_initial_death.py')
    write(str(tmp), '''import json,tempfile,unittest
from pathlib import Path
from intelligence_compiler import ingest_raw,initialize_job,process_next
class InitialDeath(unittest.TestCase):
    def test_later_failure_must_not_erase_success_or_main_completion(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); rec={'observations':[{'id':'a'},{'id':'b'}]}; ingest_raw(r,rec); initialize_job(r,'raw',1,2)
            process_next(r,'raw',lambda x:{'ok':True})
            def boom(x): raise RuntimeError('poison')
            m=process_next(r,'raw',boom)
            self.assertEqual(m['chunks'][0]['status'],'COMPLETED')
            self.assertTrue(m['main_work_completed'])
''')
    cp = run('python', '-m', 'unittest', 'tests._frz000013_initial_death', '-v', check=False)
    if cp.returncode == 0:
        raise RuntimeError('initial C candidate unexpectedly survived destructive test')
    tmp.unlink()


def materialize_survivor() -> None:
    core = r'''from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

COMPILER_VERSION = 'v1'
CHUNK_STATES = {'PENDING','COMPLETED','QUARANTINED'}

class CompilerValidationError(ValueError):
    pass

def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',',':')).encode('utf-8')

def fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()

def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_bytes(_canonical(value) + b'\n')
    tmp.replace(path)

def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))

def _validate_raw_record(record: dict[str,Any]) -> None:
    required = {'task_id','main_work_completed','outcome','evidence_refs','observations'}
    if set(record) != required:
        raise CompilerValidationError(f'raw record keys must be exact: {sorted(required)}')
    if not isinstance(record['task_id'],str) or not record['task_id']:
        raise CompilerValidationError('task_id required')
    if record['main_work_completed'] is not True:
        raise CompilerValidationError('compiler accepts only completed main work')
    if not isinstance(record['outcome'],str) or not record['outcome']:
        raise CompilerValidationError('outcome required')
    if not isinstance(record['evidence_refs'],list) or not all(isinstance(x,str) for x in record['evidence_refs']):
        raise CompilerValidationError('evidence_refs must be list[str]')
    obs = record['observations']
    if not isinstance(obs,list) or not obs:
        raise CompilerValidationError('observations must be non-empty list')
    ids=[]
    for item in obs:
        if set(item) != {'observation_id','text'} or not all(isinstance(item[k],str) and item[k] for k in item):
            raise CompilerValidationError('each observation requires observation_id/text')
        ids.append(item['observation_id'])
    if len(ids) != len(set(ids)):
        raise CompilerValidationError('duplicate observation_id')

def ingest_raw(store_root: str|Path, record: dict[str,Any]) -> dict[str,Any]:
    _validate_raw_record(record)
    root=Path(store_root)
    fp=fingerprint(record)
    raw_id='raw-'+fp[:16]
    path=root/'raw'/f'{raw_id}.json'
    envelope={'schema_version':1,'raw_id':raw_id,'raw_fingerprint':fp,'record':record}
    if path.exists():
        if _read_json(path) != envelope:
            raise CompilerValidationError('raw identity collision or mutation')
    else:
        _write_json(path,envelope)
    return {'raw_id':raw_id,'raw_fingerprint':fp,'path':str(path)}

def _raw_path(root:Path, raw_id:str)->Path:
    return root/'raw'/f'{raw_id}.json'

def _manifest_path(root:Path, raw_id:str)->Path:
    return root/'jobs'/raw_id/'manifest.json'

def initialize_job(store_root: str|Path, raw_id: str, chunk_size: int=2, max_retries: int=2) -> dict[str,Any]:
    if chunk_size < 1 or max_retries < 1:
        raise CompilerValidationError('chunk_size/max_retries must be >=1')
    root=Path(store_root); rawp=_raw_path(root,raw_id)
    if not rawp.is_file(): raise CompilerValidationError('raw must be persisted before job initialization')
    envelope=_read_json(rawp); record=envelope['record']; _validate_raw_record(record)
    if fingerprint(record) != envelope['raw_fingerprint'] or raw_id != 'raw-'+envelope['raw_fingerprint'][:16]:
        raise CompilerValidationError('raw fingerprint mismatch')
    mp=_manifest_path(root,raw_id)
    if mp.exists():
        existing=_read_json(mp)
        if existing['raw_fingerprint'] != envelope['raw_fingerprint'] or existing['compiler_version'] != COMPILER_VERSION:
            raise CompilerValidationError('existing manifest identity mismatch')
        return existing
    chunks=[]
    obs=record['observations']
    for index,start in enumerate(range(0,len(obs),chunk_size)):
        values=obs[start:start+chunk_size]
        input_fp=fingerprint(values)
        chunk_id=f'{raw_id}-chunk-{index:04d}'
        chunks.append({'index':index,'chunk_id':chunk_id,'observation_ids':[x['observation_id'] for x in values],'input_fingerprint':input_fp,'idempotency_key':fingerprint({'compiler_version':COMPILER_VERSION,'raw_fingerprint':envelope['raw_fingerprint'],'index':index,'input_fingerprint':input_fp}),'status':'PENDING','attempts':0,'result_path':None,'result_fingerprint':None,'last_error':None})
    manifest={'schema_version':1,'job_id':raw_id,'compiler_version':COMPILER_VERSION,'raw_fingerprint':envelope['raw_fingerprint'],'chunk_size':chunk_size,'max_retries':max_retries,'main_work_completed':True,'learning_status':'PENDING','application_authority':'NONE','promotion_authority':'NONE','chunks':chunks}
    _write_json(mp,manifest); return manifest

def load_manifest(store_root: str|Path, raw_id:str)->dict[str,Any]:
    p=_manifest_path(Path(store_root),raw_id)
    if not p.is_file(): raise CompilerValidationError('manifest missing')
    return _read_json(p)

def _chunk_values(root:Path, manifest:dict[str,Any], chunk:dict[str,Any])->list[dict[str,str]]:
    env=_read_json(_raw_path(root,manifest['job_id']))
    by_id={x['observation_id']:x for x in env['record']['observations']}
    try: values=[by_id[x] for x in chunk['observation_ids']]
    except KeyError as exc: raise CompilerValidationError(f'observation missing from raw: {exc}') from exc
    if fingerprint(values) != chunk['input_fingerprint']:
        raise CompilerValidationError('chunk input fingerprint mismatch')
    return values

def _result_path(root:Path, raw_id:str, chunk_id:str)->Path:
    return root/'jobs'/raw_id/'results'/f'{chunk_id}.json'

def process_next(store_root: str|Path, raw_id:str, processor:Callable[[list[dict[str,str]]],dict[str,Any]])->dict[str,Any]:
    root=Path(store_root); mp=_manifest_path(root,raw_id); manifest=load_manifest(root,raw_id)
    verify_job(root,raw_id,allow_incomplete=True)
    chunk=next((c for c in manifest['chunks'] if c['status']=='PENDING'),None)
    if chunk is None:
        manifest['learning_status']='PARTIAL_WITH_QUARANTINE' if any(c['status']=='QUARANTINED' for c in manifest['chunks']) else 'COMPLETED'
        _write_json(mp,manifest)
        return {'processed':False,'learning_status':manifest['learning_status'],'main_work_completed':True}
    rp=_result_path(root,raw_id,chunk['chunk_id'])
    if rp.exists():
        result=_read_json(rp)
        if result.get('idempotency_key') != chunk['idempotency_key']:
            raise CompilerValidationError('orphan result idempotency mismatch')
        chunk['status']='COMPLETED'; chunk['result_path']=str(rp.relative_to(root)); chunk['result_fingerprint']=fingerprint(result); chunk['last_error']=None
        manifest['learning_status']='COMPLETED' if all(c['status']=='COMPLETED' for c in manifest['chunks']) else 'PARTIAL_COMMITTED'
        _write_json(mp,manifest)
        return {'processed':False,'recovered_result':True,'chunk_id':chunk['chunk_id'],'learning_status':manifest['learning_status'],'main_work_completed':True}
    chunk['attempts'] += 1
    _write_json(mp,manifest)
    values=_chunk_values(root,manifest,chunk)
    try:
        proposal=processor(values)
        if not isinstance(proposal,dict): raise CompilerValidationError('processor output must be dict')
        for key in ('application_authority','promotion_authority','execution_authority'):
            if key in proposal and proposal[key] != 'NONE': raise CompilerValidationError('processor cannot grant authority')
        result={'schema_version':1,'chunk_id':chunk['chunk_id'],'idempotency_key':chunk['idempotency_key'],'input_fingerprint':chunk['input_fingerprint'],'proposal':proposal,'application_authority':'NONE','promotion_authority':'NONE'}
        _write_json(rp,result)
        chunk['status']='COMPLETED'; chunk['result_path']=str(rp.relative_to(root)); chunk['result_fingerprint']=fingerprint(result); chunk['last_error']=None
        manifest['learning_status']='COMPLETED' if all(c['status']=='COMPLETED' for c in manifest['chunks']) else 'PARTIAL_COMMITTED'
        _write_json(mp,manifest)
        return {'processed':True,'chunk_id':chunk['chunk_id'],'status':'COMPLETED','learning_status':manifest['learning_status'],'main_work_completed':True}
    except Exception as exc:
        chunk['last_error']=f'{type(exc).__name__}: {exc}'
        chunk['status']='QUARANTINED' if chunk['attempts'] >= manifest['max_retries'] else 'PENDING'
        manifest['learning_status']='PARTIAL_WITH_QUARANTINE' if chunk['status']=='QUARANTINED' else 'RETRY_PENDING'
        _write_json(mp,manifest)
        return {'processed':True,'chunk_id':chunk['chunk_id'],'status':chunk['status'],'learning_status':manifest['learning_status'],'main_work_completed':True,'error':chunk['last_error']}

def verify_job(store_root: str|Path, raw_id:str, allow_incomplete:bool=False)->dict[str,Any]:
    root=Path(store_root); env=_read_json(_raw_path(root,raw_id)); record=env['record']; _validate_raw_record(record)
    if fingerprint(record) != env['raw_fingerprint'] or raw_id != env['raw_id']:
        raise CompilerValidationError('raw tampered')
    m=load_manifest(root,raw_id)
    if m['raw_fingerprint'] != env['raw_fingerprint'] or m['compiler_version'] != COMPILER_VERSION:
        raise CompilerValidationError('manifest identity mismatch')
    if m.get('main_work_completed') is not True: raise CompilerValidationError('learning cannot invalidate completed main work')
    if m.get('application_authority')!='NONE' or m.get('promotion_authority')!='NONE': raise CompilerValidationError('compiler is proposal-only')
    completed=quarantined=pending=0
    for c in m['chunks']:
        if c['status'] not in CHUNK_STATES: raise CompilerValidationError('invalid chunk state')
        values=_chunk_values(root,m,c)
        expected=fingerprint({'compiler_version':COMPILER_VERSION,'raw_fingerprint':env['raw_fingerprint'],'index':c['index'],'input_fingerprint':fingerprint(values)})
        if c['idempotency_key'] != expected: raise CompilerValidationError('idempotency key mismatch')
        if c['status']=='COMPLETED':
            completed+=1
            if not c['result_path']: raise CompilerValidationError('completed chunk missing result path')
            rp=root/c['result_path']
            if not rp.is_file(): raise CompilerValidationError('completed result missing')
            result=_read_json(rp)
            if fingerprint(result) != c['result_fingerprint'] or result.get('idempotency_key') != c['idempotency_key']:
                raise CompilerValidationError('result fingerprint/idempotency mismatch')
            if result.get('application_authority')!='NONE' or result.get('promotion_authority')!='NONE': raise CompilerValidationError('result granted authority')
        elif c['status']=='QUARANTINED': quarantined+=1
        else: pending+=1
    if not allow_incomplete and pending:
        raise CompilerValidationError('job still has pending chunks')
    return {'valid':True,'job_id':raw_id,'completed_chunks':completed,'quarantined_chunks':quarantined,'pending_chunks':pending,'main_work_completed':True,'application_authority':'NONE','promotion_authority':'NONE'}

def plan_differential_reevaluation(changed_observation_ids:list[str], decision_sources:dict[str,list[str]])->dict[str,Any]:
    changed=set(changed_observation_ids)
    affected=sorted(k for k,v in decision_sources.items() if changed.intersection(v))
    return {'mode':'DIFFERENTIAL','changed_observation_ids':sorted(changed),'affected_decision_ids':affected,'full_recompile':False,'application_authority':'NONE','promotion_authority':'NONE'}

def plan_full_recompile(reason:str)->dict[str,Any]:
    if not isinstance(reason,str) or not reason.strip(): raise CompilerValidationError('full recompile requires explicit reason')
    return {'mode':'FULL_RECOMPILE','reason':reason.strip(),'full_recompile':True,'application_authority':'NONE','promotion_authority':'NONE'}
'''
    write('intelligence_compiler/core.py', core)
    write('intelligence_compiler/__init__.py', '''from .core import COMPILER_VERSION, CompilerValidationError, fingerprint, ingest_raw, initialize_job, load_manifest, process_next, verify_job, plan_differential_reevaluation, plan_full_recompile
__all__=['COMPILER_VERSION','CompilerValidationError','fingerprint','ingest_raw','initialize_job','load_manifest','process_next','verify_job','plan_differential_reevaluation','plan_full_recompile']
''')
    write('intelligence_compiler/cli.py', '''from __future__ import annotations
import argparse,json
from .core import load_manifest,verify_job

def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    v=sub.add_parser('verify'); v.add_argument('--store',default='intelligence/compiler_sample'); v.add_argument('--job')
    n=sub.add_parser('next'); n.add_argument('--store',default='intelligence/compiler_sample'); n.add_argument('--job',required=True)
    a=p.parse_args(argv)
    if a.cmd=='verify':
        job=a.job
        if not job:
            from pathlib import Path
            manifests=list(Path(a.store).glob('jobs/*/manifest.json'))
            if len(manifests)!=1: raise SystemExit('specify --job')
            job=manifests[0].parent.name
        out=verify_job(a.store,job)
    else:
        m=load_manifest(a.store,a.job); c=next((x for x in m['chunks'] if x['status']=='PENDING'),None); out={'next_chunk_id':None if c is None else c['chunk_id'],'learning_status':m['learning_status'],'application_authority':'NONE','promotion_authority':'NONE'}
    print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True))
''')
    write('intelligence_compiler/__main__.py', 'from .cli import main\nmain()\n')
    write('intelligence_compiler/README.md', '''# Incremental / Resumable Intelligence Compiler v1

Completed main work is persisted as raw outcome/evidence before learning begins. Learning is deterministic and chunked. Each successful chunk commits independently; later failures retry or quarantine only the failed chunk. Replays skip completed work by idempotency identity, and an orphan result can be adopted after a crash between result-write and manifest-update.

`LEARNING FAILURE != MAIN TASK FAILURE`

`RESUME != RECOMPUTE SUCCESSFUL CHUNKS`

`COMPILER OUTPUT = PROPOSAL ONLY`
''')


def materialize_tests_and_sample() -> str:
    write('tests/test_intelligence_compiler.py', r'''import json,tempfile,unittest
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
''')
    write('tests/test_intelligence_compiler_da.py', r'''import json,tempfile,unittest
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
''')
    store=Path('intelligence/compiler_sample')
    if store.exists(): shutil.rmtree(store)
    from intelligence_compiler import ingest_raw,initialize_job,process_next,verify_job
    record={'task_id':'frz-000013-sample','main_work_completed':True,'outcome':'sample completed task','evidence_refs':['thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000012_2026-08-27.md'],'observations':[{'observation_id':'sample-1','text':'Persist raw before learning.'},{'observation_id':'sample-2','text':'Preserve successful checkpoints.'},{'observation_id':'sample-3','text':'Quarantine poison chunks independently.'}]}
    raw=ingest_raw(store,record); initialize_job(store,raw['raw_id'],2,2)
    process_next(store,raw['raw_id'],lambda xs:{'candidate_decisions':[x['text'] for x in xs]})
    process_next(store,raw['raw_id'],lambda xs:{'candidate_decisions':[x['text'] for x in xs]})
    verify_job(store,raw['raw_id'])
    return raw['raw_id']


def validate_survivor(sample_job: str) -> None:
    run('python', '-m', 'intelligence_compiler', 'verify', '--store', 'intelligence/compiler_sample', '--job', sample_job)
    run('python', '-m', 'unittest', 'tests.test_intelligence_compiler', 'tests.test_intelligence_compiler_da', '-v')
    run('python', '-m', 'unittest', 'tests.test_restart_surface', 'tests.test_restart_surface_da', '-v')
    run('python', '-m', 'unittest', 'tests.test_selective_recall', 'tests.test_selective_recall_da', '-v')
    run('python', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_freezer*.py', '-v')
    run('python', '-m', 'freezer.cli', 'verify')
    run('python', '-m', 'freezer.build_assessment', 'verify')


def close_and_record(sample_job: str) -> None:
    meteor = f'''# FRZ-000013 — Incremental / Resumable Intelligence Compiler v1 — METEOR Result

Status: **REPOSITORY_METEOR_SURVIVOR / LOCAL_VERIFICATION_BOUNDARY**

Initial destructive candidate death: Actions run `{os.environ.get('GITHUB_RUN_ID','UNKNOWN')}`. The naive compiler reset successful chunks and flipped completed main work to incomplete when a later chunk failed.

Survivor boundary: raw-first persistence, deterministic chunks, independent result checkpoints, first-incomplete resume, idempotency identity, retry then chunk-local quarantine, orphan-result adoption, differential reevaluation, explicit full-recompile reason, and permanent proposal-only authority.

Permanent DA proves later learning failure cannot erase successful checkpoints or invalidate completed main work.

Deployment Identity is not applicable: repository-local library/CLI only. Equivalent verification boundary is committed sample + deterministic fingerprints/checkpoints + destructive tests + FREEZER governance verification.
'''
    write('thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000013_2026-08-27.md', meteor)
    write_json('/tmp/c-verified.json', {'status': 'VERIFIED'})
    run('python', '-m', 'freezer.cli', 'revise', ITEM, '--input', '/tmp/c-verified.json')
    write_json('/tmp/c-completed.json', {'status': 'COMPLETED'})
    run('python', '-m', 'freezer.cli', 'revise', ITEM, '--input', '/tmp/c-completed.json')
    run('python', '-m', 'freezer.cli', 'reindex')
    run('python', '-m', 'freezer.build_assessment', 'reindex')
    validate_survivor(sample_job)
    assert current('RTS-FRZ-000011')['status'] == 'COMPLETED'
    assert current('RTS-FRZ-000012')['status'] == 'COMPLETED'
    assert current(ITEM)['status'] == 'COMPLETED'
    for i in ('RTS-FRZ-000014', 'RTS-FRZ-000015'):
        x=current(i); assert x['status']=='FROZEN' and x['build_authority']=='NOT_APPROVED', x


def commit_survivor() -> None:
    run('git', 'config', 'user.name', 'github-actions[bot]')
    run('git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    paths=['docs/implementation/frz000013_inputs','docs/implementation/FRZ_000013_INCREMENTAL_RESUMABLE_INTELLIGENCE_COMPILER_V1_TASK.md','freezer','intelligence_compiler','intelligence/compiler_sample','tests/test_intelligence_compiler.py','tests/test_intelligence_compiler_da.py','thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000013_2026-08-27.md']
    run('git','add',*paths)
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines()
    forbidden=[p for p in staged if p.startswith('.github/workflows/') or p=='scripts/run_frz000013_ultimate_loop.py']
    if forbidden: raise RuntimeError(f'forbidden staged paths: {forbidden}')
    run('git','commit','-m','feat: complete FRZ-000013 resumable intelligence compiler v1')
    run('git','push','origin',f'HEAD:{BRANCH}')


def main() -> None:
    assert_start()
    materialize_governance()
    govern_to_wip()
    prove_initial_death()
    materialize_survivor()
    sample_job=materialize_tests_and_sample()
    validate_survivor(sample_job)
    close_and_record(sample_job)
    commit_survivor()


if __name__ == '__main__':
    main()
