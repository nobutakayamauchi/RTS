from __future__ import annotations
import copy,re
from pathlib import Path
from .core import ProofEngineError,fingerprint,load

P=Path(__file__).resolve().parent; R=P.parent; D=P/"product_readiness/round_0005"
PATH={"contract":D/"privacy_contract.json","fixtures":D/"adversarial_fixtures.json","probe_v1":D/"privacy_probe_v1.json","correction":D/"correction_log.json","probe_v2":D/"privacy_probe_v2.json","metrics":D/"operating_metrics.json","assessment":D/"readiness_reassessment.json","completion":D/"hardening_completion.json","status":R/"docs/status/RTS_CURRENT_POSITION_HARD_005.json","checkpoint":R/"pilot_runs/reconnect_pilot_p3/evidence_report_hardening_complete_checkpoint_0026.json"}
FP={'contract': '204b0214f48c4589f85fa922d885e9fa0cba1f55e75683eca70ddc3efa83c223', 'fixtures': 'bd5bb9666c4629870d4dff46281d2e35ac7b197fdfc5fb80067f9259c117e03f', 'probe_v1': '373aa3cf3ca2ede1ffe3e654e181079a62c05b1a0410a4b35cc15fd32c301269', 'correction': 'c5591afea5fd8a8f46b231cad83b58309f8f9662160b32326d3e017ca46915c9', 'probe_v2': '6b5cb0ed25205eb35ddb81ac939b03216f42109a9195959a83d9f2d0db765e27', 'metrics': '2545167da926b90ab522810b6ad252ffe5b1f82903591f79120476963f5f038e', 'assessment': '65a17e83bdc77500492ddebc0fc8df73c6dd4cd3bd387cc7d3890b1f2add7720', 'completion': 'c17c61f90eecb2c1d47202b494a335361983df7747275113e2aa08956591af3d', 'status': 'fd055f478a39f2f666c20354d7b3e8ec885ae5b1409282ae43b3b3570714f880', 'checkpoint': '9c9411680846f8efc366438f0e7c7441c2caf14ecd290f96d8db3c4578c3cd84'}
CLOSED={"customer_pilot_authorized","customer_intake_authorized","pricing_authorized","outreach_authorized","contract_authorized","delivery_authorized","publication_authorized","external_execution_authorized","source_repository_write_authorized","target_repository_write_authorized"}
STOP=[("PASSWORD",r"(?i)\b(?:password|passwd|pwd)\s*[:=]\s*\S+"),("BEARER_TOKEN",r"(?i)\bauthorization\s*:\s*bearer\s+\S+"),("PRIVATE_KEY",r"-----BEGIN TEST PRIVATE KEY-----.*?-----END TEST PRIVATE KEY-----")]
EXCLUDE=[("MY_NUMBER_STYLE",r"\b\d{4}[- ]\d{4}[- ]\d{4}\b"),("PAYMENT_CARD_STYLE",r"\b\d{4} \d{4} \d{4} \d{4}\b")]
MASK=[("EMAIL",r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),("PHONE",r"\b0\d{1,4}-\d{1,4}-\d{3,4}\b"),("FULL_NAME",r"(?:氏名|名前)\s*[:：]\s*[^\s]+"),("ADDRESS",r"(?:住所)\s*[:：]\s*[^\s]+"),("IP_ADDRESS",r"\b(?:\d{1,3}\.){3}\d{1,3}\b")]

def _s(k,v,f):
 v=load(PATH[k]) if v is None else copy.deepcopy(v); m=copy.deepcopy(v); a=m.pop(f,None)
 if a!=FP[k] or fingerprint(m)!=a: raise ProofEngineError(k+" fingerprint mismatch")
 return v
def _closed(a):
 if not CLOSED.issubset(a) or any(a[x] is not False for x in CLOSED): raise ProofEngineError("authority widened")
def _groups(ver):
 if ver not in (1,2): raise ProofEngineError("detector version")
 st=STOP+[( "CLIENT_SECRET",r"(?i)\bclient[_-]?secret\s*[:=]\s*\S+" if ver==1 else r"(?i)\bclient[\s_-]*secret\s*[:=]\s*\S+")]
 ma=MASK+([("OBFUSCATED_EMAIL",r"\b[A-Za-z0-9._%+-]+\s*\[at\]\s*[A-Za-z0-9.-]+\s*\[dot\]\s*[A-Za-z]{2,}\b")] if ver==2 else [])
 return [[(n,re.compile(p,re.I)) for n,p in g] for g in (st,EXCLUDE,ma)]
def residual_findings(t):
 return [] if t is None else sorted({n for g in _groups(2) for n,p in g if p.search(t)})
def scan_text(t,*,detector_version=2):
 st,ex,ma=_groups(detector_version); h=[n for n,p in st if p.search(t)]
 if h:return {"action":"STOP","detectors":h,"sanitized_output":None,"residual_findings":[]}
 h=[n for n,p in ex if p.search(t)]
 if h:return {"action":"EXCLUDE","detectors":h,"sanitized_output":None,"residual_findings":[]}
 o=t;h=[]
 for n,p in ma:
  if p.search(o):h.append(n);o=p.sub(f"[REDACTED_{n}]",o)
 return {"action":"MASK" if h else "ALLOW","detectors":h,"sanitized_output":o,"residual_findings":residual_findings(o)}

def verify_contract(v=None):
 v=_s("contract",v,"contract_fingerprint"); a=v["acceptance"]
 if v["work_id"]!="HARD-005" or tuple(a[x] for x in ("fixture_count","first_pass_failures_expected","final_pass_failures_required","final_residual_findings_required","raw_payloads_in_probe_results_required"))!=(12,2,0,0,0):raise ProofEngineError("contract")
 if tuple(a[x] for x in ("credential_actions_required","high_risk_identifier_actions_required","maskable_actions_required","safe_actions_required"))!=("STOP","EXCLUDE","MASK","ALLOW"):raise ProofEngineError("actions")
 if not all(a[x] is True for x in ("elapsed_time_measurement_required","manual_step_measurement_required","correction_measurement_required")):raise ProofEngineError("measurement")
 if v["authority"].get("bounded_internal_privacy_test_authorized") is not True:raise ProofEngineError("privacy authority")
 _closed(v["authority"]);return v
def verify_fixtures(v=None):
 v=_s("fixtures",v,"pack_fingerprint");xs=v["fixtures"]
 if (v["synthetic_only"],v["contains_real_personal_data"],v["contains_real_credentials"],len(xs))!=(True,False,False,12):raise ProofEngineError("fixtures")
 if [x["fixture_id"] for x in xs]!=[f"P-{i:03d}" for i in range(1,13)]:raise ProofEngineError("ids")
 fs=("fixture_id","category","input","expected_action","expected_detectors")
 if any(x["fixture_fingerprint"]!=fingerprint({f:x[f] for f in fs}) for x in xs):raise ProofEngineError("fixture fingerprint")
 return v
def _expected(x,ver):
 s=scan_text(x["input"],detector_version=ver);p=s["sanitized_output"] if s["action"]=="MASK" else None
 return {"fixture_id":x["fixture_id"],"fixture_fingerprint":x["fixture_fingerprint"],"expected_action":x["expected_action"],"actual_action":s["action"],"detectors":s["detectors"],"sanitized_output":p,"sanitized_output_fingerprint":fingerprint(s["sanitized_output"]) if s["sanitized_output"] is not None else None,"residual_findings":s["residual_findings"],"raw_input_included":False,"pass":s["action"]==x["expected_action"] and not s["residual_findings"]}
def _probe(k,v,ver,fail):
 v=_s(k,v,"probe_fingerprint"); e=[_expected(x,ver) for x in verify_fixtures()["fixtures"]]
 if v["detector_version"]!=ver or v["results"]!=e or v["failed_fixture_ids"]!=fail or (v["failure_count"],v["pass_count"])!=(len(fail),12-len(fail)):raise ProofEngineError(k)
 if v["protected_raw_payloads_persisted"]!=0 or any(x["raw_input_included"] is not False for x in v["results"]):raise ProofEngineError("raw")
 return v
def verify_probe_v1(v=None):return _probe("probe_v1",v,1,["P-009","P-012"])
def verify_correction_log(v=None):
 v=_s("correction",v,"log_fingerprint")
 if v["source_probe_fingerprint"]!=FP["probe_v1"] or v["correction_count"]!=2 or [x["fixture_id"] for x in v["entries"]]!=["P-009","P-012"] or v["append_only"] is not True or v["raw_fixture_content_repeated"] is not False:raise ProofEngineError("correction")
 return v
def verify_probe_v2(v=None):
 v=_probe("probe_v2",v,2,[])
 if v["supersedes_probe_fingerprint"]!=FP["probe_v1"] or v["correction_log_fingerprint"]!=FP["correction"]:raise ProofEngineError("lineage")
 c={a:sum(x["actual_action"]==a for x in v["results"]) for a in ("STOP","EXCLUDE","MASK","ALLOW")}
 if c!={"STOP":4,"EXCLUDE":2,"MASK":5,"ALLOW":1} or any(x["residual_findings"] for x in v["results"]):raise ProofEngineError("final probe")
 return v
def verify_metrics(v=None):
 v=_s("metrics",v,"metrics_fingerprint");b=v["automated_benchmark"];p=v["operator_process"]
 if b!={"iterations":2000,"fixture_count_per_iteration":12,"total_scans":24000,"elapsed_nanoseconds":225975547,"elapsed_milliseconds":225.976,"mean_microseconds_per_fixture":9.416,"estimated_milliseconds_per_full_pack":0.113}:raise ProofEngineError("elapsed")
 if tuple(p[x] for x in ("manual_steps","manual_interventions","correction_count","first_pass_failures","final_pass_failures"))!=(5,2,2,2,0):raise ProofEngineError("operator")
 if v["final_action_counts"]!={"STOP":4,"EXCLUDE":2,"MASK":5,"ALLOW":1} or v["residual_findings"]!=0 or v["protected_raw_payloads_persisted"]!=0:raise ProofEngineError("metrics")
 if v["interpretation"]!="MEASURED_INTERNAL_SYNTHETIC_BASELINE_NOT_A_CUSTOMER_OR_PRODUCTION_SLA":raise ProofEngineError("overclaim")
 return v
def verify_reassessment(v=None):
 v=_s("assessment",v,"assessment_fingerprint");d=v["dimension_results"];scores=[15,15,15,10,9,10,10,4,5,0]
 if [x["id"] for x in d]!=[f"PRD-{i:02d}" for i in range(1,11)] or [x["score"] for x in d]!=scores:raise ProofEngineError("dimensions")
 if (v["weighted_score"],v["score_change_from_baseline"],v["dimension_result_counts"])!=(93,11,{"PASS":7,"PARTIAL":2,"NOT_STARTED":1}):raise ProofEngineError("score")
 if any(v[x] is not False for x in ("customer_pilot_ready","production_service_ready","commercial_readiness_proven")):raise ProofEngineError("readiness")
 if (v["completion_estimates"]["overall_rts"]["percent"],v["completion_estimates"]["short_term_target"]["percent"])!=(76,100):raise ProofEngineError("completion")
 t=v["terminal"]
 if (t["state"],t["next_gate"],t["customer_pilot_status"])!=("INTERNAL_PRODUCT_HARDENING_COMPLETE","HUMAN_BOUNDED_CUSTOMER_PILOT_PLANNING_REVIEW_REQUIRED","NOT_AUTHORIZED"):raise ProofEngineError("terminal")
 return v
def verify_completion(v=None):
 v=_s("completion",v,"completion_fingerprint")
 if [x["work_id"] for x in v["work_items"]]!=[f"HARD-00{i}" for i in range(1,6)] or len(v["hard_005_acceptance"])!=10 or any(x["result"]!="PASS" for x in v["hard_005_acceptance"]):raise ProofEngineError("hardening")
 if tuple(v[x] for x in ("short_term_completion_percent","rts_overall_planning_estimate_percent","product_readiness_score"))!=(100,76,93):raise ProofEngineError("values")
 if (v["state"],v["next_gate"])!=("INTERNAL_PRODUCT_HARDENING_COMPLETE","HUMAN_BOUNDED_CUSTOMER_PILOT_PLANNING_REVIEW_REQUIRED"):raise ProofEngineError("state")
 _closed(v["authority"]);return v
def verify_progress(v=None):
 v=_s("status",v,"map_fingerprint");a=v["final_shape"]["axes"];c=v["current_position"]
 if (sum(x["score"] for x in a),sum(x["maximum"] for x in a))!=(76,100):raise ProofEngineError("progress")
 if tuple(c[x] for x in ("short_term_completion_percent","product_readiness_score","current_state"))!=(100,93,"INTERNAL_PRODUCT_HARDENING_COMPLETE"):raise ProofEngineError("position")
 if c["completed"]!=[f"HARD-00{i}" for i in range(1,6)] or c["next_steps"]!=[]:raise ProofEngineError("order")
 _closed(v["authority"]);return v
def verify_checkpoint(v=None):
 v=_s("checkpoint",v,"checkpoint_fingerprint");bind={"privacy_contract_fingerprint":"contract","fixture_pack_fingerprint":"fixtures","probe_v1_fingerprint":"probe_v1","correction_log_fingerprint":"correction","probe_v2_fingerprint":"probe_v2","operating_metrics_fingerprint":"metrics","readiness_reassessment_fingerprint":"assessment","hardening_completion_fingerprint":"completion","progress_map_fingerprint":"status"}
 if any(v[f]!=FP[k] for f,k in bind.items()) or tuple(v[x] for x in ("rts_overall_planning_estimate_percent","short_term_completion_percent","product_readiness_score"))!=(76,100,93):raise ProofEngineError("checkpoint")
 if any(v[x] is not False for x in v if x.endswith("_performed")):raise ProofEngineError("external")
 return v
def verify_privacy_hardening_stage():
 r={"contract":verify_contract(),"fixtures":verify_fixtures(),"probe_v1":verify_probe_v1(),"correction":verify_correction_log(),"probe_v2":verify_probe_v2(),"metrics":verify_metrics(),"assessment":verify_reassessment(),"completion":verify_completion(),"progress":verify_progress(),"checkpoint":verify_checkpoint()}
 r["summary"]={"state":"INTERNAL_PRODUCT_HARDENING_COMPLETE","next_gate":"HUMAN_BOUNDED_CUSTOMER_PILOT_PLANNING_REVIEW_REQUIRED","rts_overall_planning_estimate_percent":76,"short_term_completion_percent":100,"product_readiness_score":93,"product_readiness_score_change":11,"fixture_count":12,"first_pass_failures":2,"final_pass_failures":0,"final_residual_findings":0,"final_action_counts":{"STOP":4,"EXCLUDE":2,"MASK":5,"ALLOW":1},"automated_total_scans":24000,"automated_elapsed_milliseconds":225.976,"manual_steps":5,"manual_interventions":2,"correction_count":2,"customer_pilot_authorized":False,"production_service_ready":False,"commercial_readiness_proven":False,"remaining_hardening_work_items":[]}
 return r
