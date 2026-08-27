from __future__ import annotations

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
