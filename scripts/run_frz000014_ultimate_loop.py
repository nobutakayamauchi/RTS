from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT=Path('.')
ITEM='RTS-FRZ-000014'
BRANCH='feature/frz-000014-reuse-efficiency-knowledge-debt-metrics-v1'


def run(*args:str,check:bool=True):
    print('+',' '.join(args),flush=True)
    return subprocess.run(args,text=True,check=check)

def write(path:str,text:str):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')

def write_json(path:str,value): write(path,json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n')

def current(item_id:str):
    p=json.loads((ROOT/'freezer/items'/item_id/'current.json').read_text()); return json.loads((ROOT/p['path']).read_text())

def assert_start():
    for i in ('RTS-FRZ-000011','RTS-FRZ-000012','RTS-FRZ-000013'): assert current(i)['status']=='COMPLETED',current(i)
    d=current(ITEM); assert d['version']==1 and d['status']=='FROZEN' and d['build_authority']=='NOT_APPROVED',d
    e=current('RTS-FRZ-000015'); assert e['status']=='FROZEN' and e['build_authority']=='NOT_APPROVED',e
    active=[]
    for p in (ROOT/'freezer/items').glob('RTS-FRZ-*/current.json'):
        x=current(p.parent.name)
        if x['status']=='IN_PROGRESS': active.append(x['item_id'])
    assert active==[],active
    run('python','-m','freezer.cli','verify'); run('python','-m','freezer.build_assessment','verify')

def governance_inputs():
    base='docs/implementation/frz000014_inputs'
    assessment={
      'assessor':'RTS governed build assessment — Child D reuse efficiency + knowledge debt metrics',
      'rationale':'Child D is a read-only repository-local observability layer over explicit metric events. It keeps RTS reuse metrics separate from provider cache telemetry, preserves UNKNOWN instead of inventing zero, distinguishes MEASURED/ESTIMATED/UNKNOWN, retains units and denominators, and grants no execution or optimization authority. Completed A/B/C provide actual event classes and bounded state patterns to reuse.',
      'expected_effect':{'impact':4,'strategic_fit':5,'revenue_leverage':3,'risk_reduction':5,'recurrence':5,'confidence':5},
      'implementation':{'from_scratch_hours':10,'integration_hours':2,'validation_hours':3,'unknown_buffer_hours':1},
      'github_scan':{'performed':True,'repositories':['nobutakayamauchi/RTS'],'queries':['selective recall metrics events','restart surface active load','compiler quarantine checkpoints metrics'],'assets':[
        {'repository':'nobutakayamauchi/RTS','path':'selective_recall/','ref':'d68f83eea09085972775b94de5f575732aeac5ae','kind':'code','reuse_mode':'REFERENCE','license_status':'OWNED','estimated_hours_saved':2,'notes':'Defines recall/non-authority/freshness boundaries and retrieval event semantics.'},
        {'repository':'nobutakayamauchi/RTS','path':'restart_surface/','ref':'d68f83eea09085972775b94de5f575732aeac5ae','kind':'code','reuse_mode':'REFERENCE','license_status':'OWNED','estimated_hours_saved':2,'notes':'Defines restart active-load accounting and non-authority.'},
        {'repository':'nobutakayamauchi/RTS','path':'intelligence_compiler/','ref':'d68f83eea09085972775b94de5f575732aeac5ae','kind':'code','reuse_mode':'REFERENCE','license_status':'OWNED','estimated_hours_saved':3,'notes':'Defines quarantine/checkpoint/proposal-only event classes and deterministic validation.'},
        {'repository':'nobutakayamauchi/RTS','path':'freezer/','ref':'d68f83eea09085972775b94de5f575732aeac5ae','kind':'code','reuse_mode':'REFERENCE','license_status':'OWNED','estimated_hours_saved':1,'notes':'Reuse assessment/preflight/WIP/read-only governance.'}
      ],'gaps':['No current report keeps provider cache in a separate namespace from Decision Reuse Rate.','No current aggregator preserves missing telemetry as UNKNOWN with denominator/unit claim boundaries.']},
      'risks':['Provider cached-input ratio may be mislabeled as decision reuse.','Missing telemetry may be coerced to zero.','Estimated values may be presented as measured.','Character load may be mislabeled as token/time savings.','Metrics could accidentally become optimization authority.']
    }
    preflight={
      'outcome':'PASS','assessor':'RTS implementation preflight — Child D reuse efficiency + knowledge debt metrics',
      'rationale':'Read-only event validation and aggregation only. Every metric carries state/unit/source count and rates carry denominators. Missing/zero-denominator telemetry is UNKNOWN; ESTIMATED never upgrades to MEASURED. Provider cache is a distinct namespace. Report authority is NONE and metrics cannot mutate active goals or execution.',
      'affected_boundaries':['new reuse_metrics package','repository-local metrics sample','focused metric and destructive tests','RTS-FRZ-000014 lifecycle records'],
      'existing_assumptions':['A/B/C are COMPLETED.','Explicit event records are observations, not authority.','Character counts are not token/time savings.','Provider cache telemetry is optional and semantically distinct from RTS decision reuse.'],
      'data_migration':{'required':False,'notes':'No existing logs/memory/history are rewritten.'},
      'external_interfaces':['repository-local Python API/CLI only','no provider/network/deployment/action surface'],
      'approval_changes':['execution_authority=NONE','optimization_authority=NONE','promotion_authority=NONE','only RTS-FRZ-000014 may enter WIP'],
      'public_documents':['reuse_metrics/README.md','thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000014_2026-08-27.md'],
      'regression_tests':['cache/reuse namespace separation','missing UNKNOWN','estimated-state preservation','zero denominator UNKNOWN','units preserved','rates/counts/load aggregation','duplicate event rejection','non-authority','A/B/C and FREEZER regressions'],
      'hidden_dependencies':['stable metric vocabulary','event source identity','FREEZER WIP=1','optional provider telemetry'],
      'rollback_boundary':'Revert Child D package/sample/tests/docs/lifecycle only; preserve A/B/C and source events.',
      'completion_conditions':['Provider cache cannot populate RTS decision reuse.','Missing or zero-denominator metrics remain UNKNOWN.','Estimated values remain ESTIMATED.','Character load never claims token/time savings.','All metrics are observability-only/non-authorizing.','Focused and A/B/C/FREEZER regressions pass.','D reaches COMPLETED while E remains FROZEN/NOT_APPROVED.'],
      'decomposition':{'required':False,'child_candidates':[]},
      'risks':['A ratio without denominator can be misleading.','Mixed measured/estimated samples require measured-only claim behavior.','Metric naming drift can create false continuity.']
    }
    write_json(f'{base}/build_assessment_input.json',assessment); write_json(f'{base}/preflight_input.json',preflight)
    write_json(f'{base}/approve_selected.json',{'build_authority':'APPROVED','status':'SELECTED'}); write_json(f'{base}/start_in_progress.json',{'status':'IN_PROGRESS'})
    write('docs/implementation/FRZ_000014_REUSE_EFFICIENCY_KNOWLEDGE_DEBT_METRICS_V1_TASK.md','''# FRZ-000014 — Reuse Efficiency + Knowledge Debt Metrics v1

Read-only observability only. RTS reuse metrics and provider cache telemetry are separate namespaces. Missing telemetry is `UNKNOWN`, estimates stay `ESTIMATED`, and every ratio keeps its denominator. Character load is not a token/time-savings claim.
''')

def govern():
    b='docs/implementation/frz000014_inputs'
    run('python','-m','freezer.build_assessment','create',ITEM,'--input',f'{b}/build_assessment_input.json')
    g=json.loads(subprocess.check_output(['python','-m','freezer.build_assessment','gate',ITEM],text=True)); assert g['recommendation']=='BUILD_NOW' and g['assessment_state']=='CURRENT' and not g['selection_ready'],g
    run('python','-m','freezer.preflight','create',ITEM,'--input',f'{b}/preflight_input.json')
    run('python','-m','freezer.cli','revise',ITEM,'--input',f'{b}/approve_selected.json')
    g=json.loads(subprocess.check_output(['python','-m','freezer.build_assessment','gate',ITEM],text=True)); assert g['preflight_state']=='PASS' and g['recommendation']=='BUILD_NOW' and g['selection_ready'] is True,g
    run('python','-m','freezer.cli','revise',ITEM,'--input',f'{b}/start_in_progress.json'); run('python','-m','freezer.cli','reindex'); run('python','-m','freezer.build_assessment','reindex'); run('python','-m','freezer.cli','verify'); run('python','-m','freezer.build_assessment','verify')
    active=[p.parent.name for p in (ROOT/'freezer/items').glob('RTS-FRZ-*/current.json') if current(p.parent.name)['status']=='IN_PROGRESS']; assert active==[ITEM],active

def initial_death():
    write('reuse_metrics/__init__.py','from .core import compute_report\n')
    write('reuse_metrics/core.py','''def compute_report(events):
    cache=next((e.get('value',0) for e in events if e.get('metric')=='cached_input_ratio'),0)
    return {'rts_reuse_metrics':{'decision_reuse_rate':{'measurement_state':'MEASURED','value':cache}},'provider_cache':{'cached_input_ratio':{'measurement_state':'MEASURED','value':cache}}}
''')
    write('tests/_frz000014_initial_death.py','''import unittest
from reuse_metrics import compute_report
class InitialDeath(unittest.TestCase):
    def test_provider_cache_must_not_be_decision_reuse_and_missing_is_unknown(self):
        r=compute_report([{'metric':'cached_input_ratio','value':0.9}])
        self.assertEqual(r['rts_reuse_metrics']['decision_reuse_rate']['measurement_state'],'UNKNOWN')
        self.assertIsNone(r['rts_reuse_metrics']['decision_reuse_rate']['value'])
''')
    cp=run('python','-m','unittest','tests._frz000014_initial_death','-v',check=False)
    if cp.returncode==0: raise RuntimeError('initial D candidate unexpectedly survived')
    Path('tests/_frz000014_initial_death.py').unlink()

def survivor():
    core=r'''from __future__ import annotations

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
'''
    write('reuse_metrics/core.py',core)
    write('reuse_metrics/__init__.py','''from .core import MEASUREMENT_STATES,RATE_METRICS,COUNT_METRICS,LOAD_METRICS,RTS_METRICS,PROVIDER_METRICS,MetricsValidationError,validate_event,compute_report,validate_report,write_report
__all__=['MEASUREMENT_STATES','RATE_METRICS','COUNT_METRICS','LOAD_METRICS','RTS_METRICS','PROVIDER_METRICS','MetricsValidationError','validate_event','compute_report','validate_report','write_report']
''')
    write('reuse_metrics/cli.py','''import argparse,json
from pathlib import Path
from .core import compute_report,validate_report

def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('compute'); c.add_argument('--events',default='metrics/reuse_events.json'); c.add_argument('--output')
    v=sub.add_parser('verify'); v.add_argument('--report',default='metrics/reuse_report.json')
    a=p.parse_args(argv)
    if a.cmd=='compute':
        r=compute_report(json.loads(Path(a.events).read_text()));
        if a.output: Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
        print(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True))
    else:
        print(json.dumps(validate_report(json.loads(Path(a.report).read_text())),indent=2,sort_keys=True))
''')
    write('reuse_metrics/__main__.py','from .cli import main\nmain()\n')
    write('reuse_metrics/README.md','''# Reuse Efficiency + Knowledge Debt Metrics v1

Read-only RTS observability. Provider cache telemetry is deliberately isolated from RTS decision/failure/retrieval reuse metrics. Missing telemetry is `UNKNOWN`, estimates stay `ESTIMATED`, and rate denominators are preserved.

`CACHED INPUT RATIO != DECISION REUSE RATE`

`MISSING != ZERO`

`CHARS != TOKENS != TIME`

`METRICS != OPTIMIZATION AUTHORITY`
''')

def tests_and_sample():
    write('tests/test_reuse_metrics.py',r'''import json,unittest
from pathlib import Path
from reuse_metrics import MetricsValidationError,compute_report,validate_report

def event(i,m,state='MEASURED',n=None,d=None,v=None,unit='ratio'):
    return {'event_id':i,'metric':m,'measurement_state':state,'numerator':n,'denominator':d,'value':v,'unit':unit,'source_ref':'test'}
class ReuseMetricsTests(unittest.TestCase):
    def test_rate_aggregation_keeps_denominator(self):
        r=compute_report([event('1','decision_reuse_rate',n=3,d=4),event('2','decision_reuse_rate',n=1,d=2)])['rts_reuse_metrics']['decision_reuse_rate']; self.assertEqual(r['numerator'],4); self.assertEqual(r['denominator'],6); self.assertAlmostEqual(r['value'],4/6)
    def test_count_metrics_sum(self):
        xs=[event('1','knowledge_debt_count',v=2,unit='count'),event('2','knowledge_debt_count',v=3,unit='count')]; self.assertEqual(compute_report(xs)['rts_reuse_metrics']['knowledge_debt_count']['value'],5)
    def test_restart_load_unit_is_chars(self):
        r=compute_report([event('1','restart_surface_load',v=700,unit='chars')]); m=r['rts_reuse_metrics']['restart_surface_load']; self.assertEqual(m['unit'],'chars'); self.assertTrue(r['claim_boundaries']['restart_surface_load_is_chars_not_tokens_or_time'])
    def test_measured_wins_over_estimated_without_relabeling_estimate(self):
        xs=[event('1','failure_reuse_rate','ESTIMATED',n=8,d=10),event('2','failure_reuse_rate','MEASURED',n=1,d=2)]; m=compute_report(xs)['rts_reuse_metrics']['failure_reuse_rate']; self.assertEqual(m['measurement_state'],'MEASURED'); self.assertEqual(m['source_event_count'],1); self.assertEqual(m['value'],.5)
    def test_duplicate_event_fails(self):
        e=event('1','decision_reuse_rate',n=1,d=2)
        with self.assertRaises(MetricsValidationError): compute_report([e,e])
    def test_committed_report_valid(self): self.assertTrue(validate_report(json.loads(Path('metrics/reuse_report.json').read_text()))['valid'])
''')
    write('tests/test_reuse_metrics_da.py',r'''import unittest
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
''')
    events=[
      {'event_id':'d1','metric':'decision_reuse_rate','measurement_state':'MEASURED','numerator':3,'denominator':5,'value':None,'unit':'ratio','source_ref':'child-a-retrieval'},
      {'event_id':'f1','metric':'failure_reuse_rate','measurement_state':'MEASURED','numerator':2,'denominator':4,'value':None,'unit':'ratio','source_ref':'child-a-da'},
      {'event_id':'r1','metric':'retrieval_precision','measurement_state':'MEASURED','numerator':4,'denominator':5,'value':None,'unit':'ratio','source_ref':'child-a-retrieval'},
      {'event_id':'rc1','metric':'retrieval_changed_next_action_rate','measurement_state':'ESTIMATED','numerator':2,'denominator':5,'value':None,'unit':'ratio','source_ref':'bounded-sample'},
      {'event_id':'n1','metric':'novel_reasoning_ratio','measurement_state':'UNKNOWN','numerator':None,'denominator':None,'value':None,'unit':'ratio','source_ref':'provider-not-instrumented'},
      {'event_id':'ra1','metric':'recompute_avoidance_rate','measurement_state':'ESTIMATED','numerator':3,'denominator':6,'value':None,'unit':'ratio','source_ref':'bounded-sample'},
      {'event_id':'retry1','metric':'retry_avoidance_count','measurement_state':'MEASURED','numerator':None,'denominator':None,'value':1,'unit':'count','source_ref':'child-c-checkpoint'},
      {'event_id':'human1','metric':'human_intervention_count','measurement_state':'MEASURED','numerator':None,'denominator':None,'value':1,'unit':'count','source_ref':'ultimate-loop'},
      {'event_id':'load1','metric':'restart_surface_load','measurement_state':'MEASURED','numerator':None,'denominator':None,'value':820,'unit':'chars','source_ref':'child-b-surface'},
      {'event_id':'debt1','metric':'knowledge_debt_count','measurement_state':'MEASURED','numerator':None,'denominator':None,'value':1,'unit':'count','source_ref':'child-c-quarantine'},
      {'event_id':'prom1','metric':'promotion_candidate_count','measurement_state':'MEASURED','numerator':None,'denominator':None,'value':2,'unit':'count','source_ref':'child-c-proposals'},
      {'event_id':'q1','metric':'quarantined_learning_count','measurement_state':'MEASURED','numerator':None,'denominator':None,'value':0,'unit':'count','source_ref':'child-c-sample'},
      {'event_id':'rollback1','metric':'promotion_rollback_count','measurement_state':'UNKNOWN','numerator':None,'denominator':None,'value':None,'unit':'count','source_ref':'not-instrumented'},
      {'event_id':'cache1','metric':'cached_input_ratio','measurement_state':'MEASURED','numerator':4772,'denominator':4835,'value':None,'unit':'ratio','source_ref':'provider-sample-separate'}
    ]
    write_json('metrics/reuse_events.json',events)
    os.environ.setdefault('PYTHONPATH','.')
    from reuse_metrics import write_report
    write_report('metrics/reuse_report.json',events)

def validate():
    run('python','-m','reuse_metrics','verify','--report','metrics/reuse_report.json')
    run('python','-m','unittest','tests.test_reuse_metrics','tests.test_reuse_metrics_da','-v')
    run('python','-m','unittest','tests.test_intelligence_compiler','tests.test_intelligence_compiler_da','-v')
    run('python','-m','unittest','tests.test_restart_surface','tests.test_restart_surface_da','-v')
    run('python','-m','unittest','tests.test_selective_recall','tests.test_selective_recall_da','-v')
    run('python','-m','unittest','discover','-s','tests','-p','test_freezer*.py','-v')
    run('python','-m','freezer.cli','verify'); run('python','-m','freezer.build_assessment','verify')

def close():
    write('thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000014_2026-08-27.md',f'''# FRZ-000014 — Reuse Efficiency + Knowledge Debt Metrics v1 — METEOR Result

Status: **REPOSITORY_METEOR_SURVIVOR / LOCAL_VERIFICATION_BOUNDARY**

Initial destructive candidate death: Actions run `{os.environ.get('GITHUB_RUN_ID','UNKNOWN')}`. The naive report copied provider `cached_input_ratio` into `decision_reuse_rate` and invented measured zero for missing RTS telemetry.

Survivor boundary: RTS reuse metrics and provider cache are separate namespaces; missing/zero-denominator telemetry is UNKNOWN; estimates remain ESTIMATED; ratios retain numerators/denominators; restart load remains chars; reports grant no execution/optimization/promotion authority.

Deployment Identity is not applicable: repository-local observability library/CLI only. Equivalent boundary is committed event sample + deterministic aggregation + destructive claim-boundary tests + FREEZER verification.
''')
    write_json('/tmp/dv.json',{'status':'VERIFIED'}); run('python','-m','freezer.cli','revise',ITEM,'--input','/tmp/dv.json')
    write_json('/tmp/dc.json',{'status':'COMPLETED'}); run('python','-m','freezer.cli','revise',ITEM,'--input','/tmp/dc.json'); run('python','-m','freezer.cli','reindex'); run('python','-m','freezer.build_assessment','reindex'); validate()
    for i in ('RTS-FRZ-000011','RTS-FRZ-000012','RTS-FRZ-000013','RTS-FRZ-000014'): assert current(i)['status']=='COMPLETED',current(i)
    e=current('RTS-FRZ-000015'); assert e['status']=='FROZEN' and e['build_authority']=='NOT_APPROVED',e

def commit():
    run('git','config','user.name','github-actions[bot]'); run('git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    paths=['docs/implementation/frz000014_inputs','docs/implementation/FRZ_000014_REUSE_EFFICIENCY_KNOWLEDGE_DEBT_METRICS_V1_TASK.md','freezer','reuse_metrics','metrics/reuse_events.json','metrics/reuse_report.json','tests/test_reuse_metrics.py','tests/test_reuse_metrics_da.py','thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000014_2026-08-27.md']
    run('git','add',*paths); staged=subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines(); forbidden=[p for p in staged if p.startswith('.github/workflows/') or p=='scripts/run_frz000014_ultimate_loop.py']; assert not forbidden,forbidden
    run('git','commit','-m','feat: complete FRZ-000014 reuse efficiency metrics v1'); run('git','push','origin',f'HEAD:{BRANCH}')

def main():
    assert_start(); governance_inputs(); govern(); initial_death(); survivor(); tests_and_sample(); validate(); close(); commit()
if __name__=='__main__': main()
