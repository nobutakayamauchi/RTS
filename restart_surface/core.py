from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any

class RestartValidationError(ValueError):
    pass

RESTART_FIELDS = (
    'goal','repo','branch','commit','changed','verified','unresolved',
    'rollback','do_not_touch','next_authorized_action'
)
LIST_FIELDS = {'changed','verified','unresolved','do_not_touch'}
REOPEN_REASONS = {'OPERATOR_REQUEST','EQUIVALENCE_MISMATCH','UNRESOLVED_BLOCKER','STALE_SOURCE'}
FORBIDDEN_INLINE_KEYS = {'full_history','raw_history','transcript','body','content','history_blob'}

def git_blob_sha_bytes(data: bytes) -> str:
    return hashlib.sha1(f'blob {len(data)}\0'.encode('utf-8') + data).hexdigest()

def _contained(root: Path, rel: str) -> Path:
    p=(root/rel).resolve()
    rr=root.resolve()
    if p != rr and rr not in p.parents:
        raise RestartValidationError(f'path escapes repository: {rel}')
    return p

def _active_payload(surface: dict[str, Any]) -> dict[str, Any]:
    return {k:v for k,v in surface.items() if k != 'active_load_chars'}

def active_load_chars(surface: dict[str, Any]) -> int:
    return len(json.dumps(_active_payload(surface),sort_keys=True,ensure_ascii=False,separators=(',',':')))

def _validate_required_state(state: dict[str, Any]) -> None:
    for key in RESTART_FIELDS:
        if key not in state:
            raise RestartValidationError(f'missing restart field: {key}')
    for key in LIST_FIELDS:
        if not isinstance(state[key], list) or not all(isinstance(x,str) for x in state[key]):
            raise RestartValidationError(f'{key} must be list[str]')
    for key in set(RESTART_FIELDS)-LIST_FIELDS:
        if not isinstance(state[key],str) or not state[key]:
            raise RestartValidationError(f'{key} must be non-empty str')
    if len(state['commit']) < 7:
        raise RestartValidationError('commit identity too short')

def build_surface(repo_root: str|Path, full_state: dict[str,Any], source_refs: list[dict[str,str]], max_active_chars: int=8000) -> dict[str,Any]:
    _validate_required_state(full_state)
    surface={k:full_state[k] for k in RESTART_FIELDS}
    surface.update({
        'schema_version':1,
        'source_refs':source_refs,
        'reopen_conditions':sorted(REOPEN_REASONS),
        'selective_recall_interface':{'mode':'REQUEST_ONLY','authority':'NONE'},
        'execution_authority':'NONE',
        'promotion_authority':'NONE',
    })
    surface['active_load_chars']=active_load_chars(surface)
    if surface['active_load_chars'] > max_active_chars:
        raise RestartValidationError(f'active surface over budget: {surface["active_load_chars"]}>{max_active_chars}')
    validate_surface(repo_root,surface,max_active_chars=max_active_chars)
    return surface

def validate_surface(repo_root: str|Path, surface: dict[str,Any], max_active_chars: int=8000) -> dict[str,Any]:
    root=Path(repo_root)
    _validate_required_state(surface)
    if surface.get('schema_version') != 1:
        raise RestartValidationError('schema_version must be 1')
    if surface.get('execution_authority') != 'NONE' or surface.get('promotion_authority') != 'NONE':
        raise RestartValidationError('restart surface is non-authorizing')
    if set(surface.get('reopen_conditions',[])) != REOPEN_REASONS:
        raise RestartValidationError('reopen conditions are incomplete')
    if any(k in surface for k in FORBIDDEN_INLINE_KEYS):
        raise RestartValidationError('deep history cannot be inlined into active surface')
    refs=surface.get('source_refs')
    if not isinstance(refs,list):
        raise RestartValidationError('source_refs must be list')
    current=0
    for ref in refs:
        if set(ref) != {'path','git_blob_sha'}:
            raise RestartValidationError('source ref must contain exact path/git_blob_sha')
        p=_contained(root,ref['path'])
        if not p.is_file():
            raise RestartValidationError(f'missing source: {ref["path"]}')
        if git_blob_sha_bytes(p.read_bytes()) != ref['git_blob_sha']:
            raise RestartValidationError(f'stale source: {ref["path"]}')
        current += 1
    measured=active_load_chars(surface)
    if surface.get('active_load_chars') != measured:
        raise RestartValidationError('active_load_chars is stale')
    if measured > max_active_chars:
        raise RestartValidationError(f'active surface over budget: {measured}>{max_active_chars}')
    return {'valid':True,'active_load_chars':measured,'source_count':len(refs),'current_source_count':current,'execution_authority':'NONE','promotion_authority':'NONE'}

def restart_equivalence(full_state: dict[str,Any], surface: dict[str,Any]) -> dict[str,Any]:
    _validate_required_state(full_state)
    missing=[]; changed=[]
    for key in RESTART_FIELDS:
        if key not in surface: missing.append(key)
        elif surface[key] != full_state[key]: changed.append(key)
    return {'equivalent':not missing and not changed,'denominator':len(RESTART_FIELDS),'matched':len(RESTART_FIELDS)-len(missing)-len(changed),'missing':missing,'changed':changed}

def decide_restart(surface: dict[str,Any], request: dict[str,Any]) -> dict[str,Any]:
    reason=None
    if request.get('operator_request_full_history'): reason='OPERATOR_REQUEST'
    elif request.get('equivalence_mismatch'): reason='EQUIVALENCE_MISMATCH'
    elif request.get('unresolved_blocker'): reason='UNRESOLVED_BLOCKER'
    elif request.get('stale_source'): reason='STALE_SOURCE'
    if reason:
        return {'decision':'REOPEN_FULL_HISTORY','reason':reason,'execution_authority':'NONE','promotion_authority':'NONE'}
    if request.get('missing_detail'):
        return {'decision':'SELECTIVE_RECALL','recall_request':{'event':request.get('event','restart_detail_needed'),'scope_tags':request.get('scope_tags',[]),'max_results':1},'execution_authority':'NONE','promotion_authority':'NONE'}
    return {'decision':'CONTINUE_FROM_SURFACE','execution_authority':'NONE','promotion_authority':'NONE'}
