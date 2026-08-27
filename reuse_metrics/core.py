from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MEASUREMENT_STATES={'MEASURED','ESTIMATED','UNKNOWN'}
RATE_METRICS={'decision_reuse_rate','failure_reuse_rate','retrieval_precision','retrieval_changed_next_action_rate','novel_reasoning_ratio','recompute_avoidance_rate'}
COUNT_METRICS={'retry_avoidance_count','human_intervention_count','knowledge_debt_count','promotion_candidate_count','quarantined_learning_count','promotion_rollback_count'}
LOAD_METRICS={'restart_surface_load'}
RTS_METRICS=RATE_METRICS|COUNT_METRICS|LOAD_METRICS
PROVIDER_METRICS={'cached_input_ratio'}
ALL_METRICS=RTS_METRICS|PROVIDER_METRICS
UNITS={**{m:'ratio' for m in RATE_METRICS},**{m:'count' for m in COUNT_METRICS},'restart_surface_load':'chars','cached_input_ratio':'ratio'}

class MetricsValidationError(ValueError): pass

def validate_event(e:dict[str,Any])->None:
    required={'event_id','metric','measurement_state','numerator','denominator','value','unit','source_ref'}
    if set(e)!=required: raise MetricsValidationError(f'event keys must be exact: {sorted(required)}')
    if not isinstance(e['event_id'],str) or not e['event_id']: raise MetricsValidationError('event_id required')
    if e['metric'] not in ALL_METRICS: raise MetricsValidationError('unknown metric')
    if e['measurement_state'] not in MEASUREMENT_STATES: raise MetricsValidationError('invalid measurement_state')
    if e['unit']!=UNITS[e['metric']]: raise MetricsValidationError('unit mismatch')
    if not isinstance(e['source_ref'],str) or not e['source_ref']: raise MetricsValidationError('source_ref required')
    if e['measurement_state']=='UNKNOWN':
        if any(e[k] is not None for k in ('numerator','denominator','value')): raise MetricsValidationError('UNKNOWN cannot carry numeric claim')
        return
    if e['metric'] in RATE_METRICS|PROVIDER_METRICS:
        if not isinstance(e['numerator'],(int,float)) or not isinstance(e['denominator'],(int,float)): raise MetricsValidationError('rate requires numerator/denominator')
        if e['numerator']<0 or e['denominator']<0: raise MetricsValidationError('rate components must be nonnegative')
        if e['value'] is not None: raise MetricsValidationError('rate value is derived, not supplied')
    else:
        if e['numerator'] is not None or e['denominator'] is not None: raise MetricsValidationError('non-rate must not carry numerator/denominator')
        if not isinstance(e['value'],(int,float)) or e['value']<0: raise MetricsValidationError('value must be nonnegative number')

def _unknown(metric:str,reason:str,source_count:int=0)->dict[str,Any]:
    return {'measurement_state':'UNKNOWN','value':None,'numerator':None,'denominator':None,'unit':UNITS[metric],'source_event_count':source_count,'reason':reason}

def _aggregate_metric(metric:str,events:list[dict[str,Any]])->dict[str,Any]:
    xs=[e for e in events if e['metric']==metric]
    measured=[e for e in xs if e['measurement_state']=='MEASURED']
    estimated=[e for e in xs if e['measurement_state']=='ESTIMATED']
    chosen=measured if measured else estimated
    if not chosen: return _unknown(metric,'MISSING_TELEMETRY',len(xs))
    state='MEASURED' if measured else 'ESTIMATED'
    if metric in RATE_METRICS|PROVIDER_METRICS:
        n=sum(float(e['numerator']) for e in chosen); d=sum(float(e['denominator']) for e in chosen)
        if d<=0: return _unknown(metric,'ZERO_DENOMINATOR',len(chosen))
        return {'measurement_state':state,'value':n/d,'numerator':n,'denominator':d,'unit':UNITS[metric],'source_event_count':len(chosen),'reason':None}
    values=[float(e['value']) for e in chosen]
    if metric in COUNT_METRICS: value=sum(values)
    else: value=sum(values)/len(values)
    return {'measurement_state':state,'value':value,'numerator':None,'denominator':None,'unit':UNITS[metric],'source_event_count':len(chosen),'reason':None}

def compute_report(events:list[dict[str,Any]])->dict[str,Any]:
    ids=[]
    for e in events: validate_event(e); ids.append(e['event_id'])
    if len(ids)!=len(set(ids)): raise MetricsValidationError('duplicate event_id')
    rts={m:_aggregate_metric(m,events) for m in sorted(RTS_METRICS)}
    provider={m:_aggregate_metric(m,events) for m in sorted(PROVIDER_METRICS)}
    return {'schema_version':1,'rts_reuse_metrics':rts,'provider_cache':provider,'claim_boundaries':{'provider_cache_is_not_decision_reuse':True,'restart_surface_load_is_chars_not_tokens_or_time':True,'estimated_is_not_measured':True,'missing_is_unknown_not_zero':True},'execution_authority':'NONE','optimization_authority':'NONE','promotion_authority':'NONE'}

def validate_report(report:dict[str,Any])->dict[str,Any]:
    if report.get('execution_authority')!='NONE' or report.get('optimization_authority')!='NONE' or report.get('promotion_authority')!='NONE': raise MetricsValidationError('metrics report is non-authorizing')
    if 'cached_input_ratio' in report.get('rts_reuse_metrics',{}): raise MetricsValidationError('provider cache leaked into RTS metric namespace')
    if 'decision_reuse_rate' in report.get('provider_cache',{}): raise MetricsValidationError('decision reuse leaked into provider namespace')
    for namespace in ('rts_reuse_metrics','provider_cache'):
        for metric,value in report.get(namespace,{}).items():
            if value.get('measurement_state')=='UNKNOWN' and value.get('value') is not None: raise MetricsValidationError('UNKNOWN carried numeric value')
            if value.get('measurement_state') not in MEASUREMENT_STATES: raise MetricsValidationError('invalid report state')
            if value.get('unit')!=UNITS[metric]: raise MetricsValidationError('report unit mismatch')
    return {'valid':True,'execution_authority':'NONE','optimization_authority':'NONE','promotion_authority':'NONE'}

def write_report(path:str|Path,events:list[dict[str,Any]])->dict[str,Any]:
    report=compute_report(events); validate_report(report); p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); return report
