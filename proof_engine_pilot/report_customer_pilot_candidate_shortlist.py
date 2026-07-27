from __future__ import annotations
import copy
from pathlib import Path
from typing import Any
from .core import ProofEngineError,fingerprint,load
P=Path(__file__).resolve().parent;R=P.parent;D=P/"product_readiness/round_0008"
PATH={"contract":D/"candidate_discovery_contract.json","universe":D/"candidate_universe.json","evidence":D/"candidate_evidence_snapshot.json","scores":D/"candidate_scores.json","decision":D/"shortlist_decision.json","risk":D/"contact_risk_review.json","score_hold":D/"readiness_score_hold.json","completion":D/"candidate_shortlist_completion.json","status":R/"docs/status/RTS_CURRENT_POSITION_CANDIDATE_SHORTLIST.json","checkpoint":R/"pilot_runs/reconnect_pilot_p3/evidence_report_customer_pilot_candidate_shortlist_checkpoint_0029.json","prior_status":R/"docs/status/RTS_CURRENT_POSITION_PILOT_EXECUTION_AUTH.json","prior_checkpoint":R/"pilot_runs/reconnect_pilot_p3/evidence_report_customer_pilot_execution_auth_checkpoint_0028.json"}
FP={'contract': '64ec361b4ea0b866a9d0009c863988bf1e0ba12c455e89b8ea1183a4b4c8c221', 'universe': 'db9b5b003b28961a2a720ca856a8fd1793741cb9b8673c155e8c72c7c3baeb13', 'evidence': '00e80125a48912404978afc42403d9a5c2b0137c1cf2ac3217a92fef74bcdd6c', 'scores': '487ab0f2c34d8321c228e0b9f80b8a3001f382180ef08f52de26686c3ab23f81', 'decision': '3a9080bd457a3b795584b70baa94e18a1b6cc71b336b1db2bf1de50a493f52b5', 'risk': '8e8db09c3e5a89a63d126524d00d20f5819bbd21396356f7253230149934b179', 'score_hold': 'e35ba651d43ec7823cba5bc736915594f230255f18fb577e6acaf5c870637ad0', 'completion': '4bc4c3cb4bcf121e21887c150363035074680ebdd356d4640d412ab01790a853', 'status': '963cdcbff1c70c3c432135021fd67f0386e417571a2aaff7c9ec74d04a09042d', 'checkpoint': '42212a185a492ebc92c15a9fd90abc4e22fea0c90cae794560ef275365400861'}
PRIOR_STATUS_FP="468fbb778b4c7d271f80e082e2afbd5ec7d2daca595e1c7a020951c70249b76e";PRIOR_CHECKPOINT_FP="0fb836f70ca37d58f9b22f8cd21d487014c6eadfd2fdb16d746a29c3856a0627"
CLOSED={"participant_contact_authorized","customer_intake_authorized","customer_pilot_execution_authorized","pricing_authorized","outreach_authorized","contract_authorized","delivery_authorized","publication_authorized","external_execution_authorized","source_repository_write_authorized","target_repository_write_authorized"}
REPOS=["jbexta/AgentPilot","tmseidel/ai-git-bot","DahnM20/ai-flow"]
COMMITS={"jbexta/AgentPilot":"333eb6ce4f193852f4d9fe5412e8636929b6bb4e","tmseidel/ai-git-bot":"498d50b365407e117390bbc79fe41af0fbc2300f","DahnM20/ai-flow":"98ebab6ff3f83cc82aeac59c012824b54141ae99"}
SCORES={"CAND-001":86,"CAND-002":83,"CAND-003":72}
def _s(k,v,f):
 v=load(PATH[k]) if v is None else copy.deepcopy(v);m=copy.deepcopy(v);a=m.pop(f,None)
 if a!=FP[k] or fingerprint(m)!=a:raise ProofEngineError(k+" fingerprint mismatch")
 return v
def _c(a):
 if not CLOSED.issubset(a) or any(a[x] is not False for x in CLOSED):raise ProofEngineError("external authority widened")
def verify_prior_execution_authorization_history():
 s=load(PATH["prior_status"]);m=copy.deepcopy(s);a=m.pop("map_fingerprint",None)
 if a!=PRIOR_STATUS_FP or fingerprint(m)!=a:raise ProofEngineError("prior execution authorization status changed")
 c=load(PATH["prior_checkpoint"]);m=copy.deepcopy(c);b=m.pop("checkpoint_fingerprint",None)
 if b!=PRIOR_CHECKPOINT_FP or fingerprint(m)!=b:raise ProofEngineError("prior execution authorization checkpoint changed")
 return {"prior_status":a,"prior_checkpoint":b}
def verify_contract(v=None):
 v=_s("contract",v,"contract_fingerprint");s=v["source"]
 if (s["prior_execution_authorization_checkpoint_fingerprint"],s["prior_state"],s["raw_instruction_retained"],len(s["raw_instruction_sha256"]))!=(PRIOR_CHECKPOINT_FP,"INTERNAL_BOUNDED_CUSTOMER_PILOT_EXECUTION_AUTHORIZATION_PACKET_COMPLETE",False,64):raise ProofEngineError("prior or instruction mismatch")
 if v["scope"]!={"public_repository_only":True,"individual_account_owner_only":True,"candidate_record_count":3,"shortlist_limit":2,"recommendation_limit":1,"selected_candidate_count_required":0,"contact_event_count_required":0,"customer_intake_event_count_required":0,"pilot_execution_event_count_required":0,"minimum_public_score":80,"required_pending_human_gates":["REPOSITORY_AUTHORITY_CONFIRMATION","WRITTEN_VOLUNTARY_CONSENT"]}:raise ProofEngineError("discovery scope widened")
 if v["authorized_now"]!={"internal_public_candidate_discovery":True,"internal_public_candidate_scoring":True,"internal_candidate_recommendation":True,"named_candidate_selection":False,"participant_contact":False,"customer_intake":False,"pilot_execution":False}:raise ProofEngineError("authorization contract mismatch")
 a=v["acceptance"]
 if tuple(a[x] for x in ("artifact_count","candidate_count","shortlist_count","recommended_count","selected_count","focused_test_count_minimum","product_readiness_score_required","rts_overall_planning_estimate_percent_required","external_action_count_required"))!=(8,3,2,1,0,24,93,79,0):raise ProofEngineError("acceptance contract mismatch")
 if not all(v["authority"].get(x) is True for x in ("internal_candidate_discovery_authorized","internal_candidate_scoring_authorized","internal_candidate_recommendation_authorized")):raise ProofEngineError("internal discovery authority missing")
 _c(v["authority"]);return v
def verify_universe(v=None):
 v=_s("universe",v,"universe_fingerprint");xs=v["candidate_records"]
 if v["contract_fingerprint"]!=FP["contract"] or v["source_mode"]!="PUBLIC_GITHUB_READ_ONLY" or v["candidate_count"]!=3:raise ProofEngineError("universe boundary mismatch")
 if [x["repository"] for x in xs]!=REPOS or [x["candidate_id"] for x in xs]!=["CAND-001","CAND-002","CAND-003"]:raise ProofEngineError("candidate universe changed")
 for x in xs:
  if x["owner_type"]!="User" or x["visibility"]!="public" or x["archived"] is not False:raise ProofEngineError("candidate public individual boundary failed")
  if x["fixed_commit_sha"]!=COMMITS[x["repository"]] or len(x["readme_blob_sha"])!=40:raise ProofEngineError("candidate immutable commit mismatch")
  if x["candidate_fingerprint"]!=fingerprint({k:z for k,z in x.items() if k!="candidate_fingerprint"}):raise ProofEngineError("candidate record fingerprint mismatch")
 if [x["observed_merged_pr_sample_count"] for x in xs]!=[12,12,2]:raise ProofEngineError("merged PR sample changed")
 if any(v[x] is not False for x in ("contains_private_repository_data","contains_credentials","contains_nonpublic_personal_data","contact_performed","selection_performed")):raise ProofEngineError("private or external candidate action recorded")
 _c(v["authority"]);return v
def verify_evidence(v=None):
 v=_s("evidence",v,"snapshot_fingerprint")
 if (v["contract_fingerprint"],v["universe_fingerprint"],v["candidate_count"],v["evidence_item_count"])!=(FP["contract"],FP["universe"],3,12):raise ProofEngineError("evidence binding mismatch")
 u={x["candidate_id"]:x["candidate_fingerprint"] for x in verify_universe()["candidate_records"]}
 for r in v["records"]:
  if r["candidate_fingerprint"]!=u[r["candidate_id"]] or r["evidence_item_count"]!=4:raise ProofEngineError("evidence candidate binding mismatch")
  if len(r["withheld_conclusions"])!=5:raise ProofEngineError("withheld conclusions weakened")
  for x in r["evidence_items"]:
   if x["evidence_fingerprint"]!=fingerprint({k:z for k,z in x.items() if k!="evidence_fingerprint"}):raise ProofEngineError("evidence item fingerprint mismatch")
 if v["raw_repository_content_persisted"] is not False or v["external_action_performed"] is not False:raise ProofEngineError("raw content or external action recorded")
 _c(v["authority"]);return v
def verify_scores(v=None):
 v=_s("scores",v,"scores_fingerprint")
 if tuple(v[x] for x in ("contract_fingerprint","universe_fingerprint","snapshot_fingerprint"))!=(FP["contract"],FP["universe"],FP["evidence"]):raise ProofEngineError("scores binding mismatch")
 if sum(x["maximum"] for x in v["criteria"])!=100 or len(v["criteria"])!=7 or v["minimum_public_score"]!=80 or v["all_hard_gates_required_before_contact"] is not True:raise ProofEngineError("candidate threshold weakened")
 for r in v["score_records"]:
  if sum(x["score"] for x in r["criterion_scores"])!=r["weighted_score"]:raise ProofEngineError("candidate score sum mismatch")
  if r["weighted_score"]!=SCORES[r["candidate_id"]]:raise ProofEngineError("candidate score changed")
  if [x["id"] for x in r["hard_gate_results"]]!=[f"CG-{i:02d}" for i in range(1,9)]:raise ProofEngineError("hard gate set mismatch")
  if r["pending_human_gate_count"]!=2 or r["selected"] is not False or r["contact_authorized"] is not False:raise ProofEngineError("candidate silently selected or contacted")
  if r["score_fingerprint"]!=fingerprint({k:z for k,z in r.items() if k!="score_fingerprint"}):raise ProofEngineError("score record fingerprint mismatch")
 if v["ranking"]!=["CAND-001","CAND-002","CAND-003"]:raise ProofEngineError("ranking changed")
 if v["shortlist_candidate_ids"]!=["CAND-001","CAND-002"] or v["recommended_candidate_id"]!="CAND-001":raise ProofEngineError("shortlist changed")
 if v["selected_candidate_id"] is not None or v["participant_contact_authorized"] is not False:raise ProofEngineError("candidate selection or contact silently authorized")
 _c(v["authority"]);return v
def verify_decision(v=None):
 v=_s("decision",v,"decision_fingerprint")
 if tuple(v[x] for x in ("contract_fingerprint","universe_fingerprint","snapshot_fingerprint","scores_fingerprint"))!=(FP["contract"],FP["universe"],FP["evidence"],FP["scores"]):raise ProofEngineError("decision binding mismatch")
 r=v["recommended_candidate"]
 if (v["decision"],r["candidate_id"],r["repository"],r["weighted_score"],r["status"])!=("INTERNAL_PUBLIC_CANDIDATE_SHORTLIST_COMPLETE","CAND-001","jbexta/AgentPilot",86,"RECOMMENDED_FOR_HUMAN_SELECTION_REVIEW_NOT_SELECTED"):raise ProofEngineError("recommended candidate changed")
 if v["reserve_candidate"]["candidate_id"]!="CAND-002" or v["held_candidate"]["candidate_id"]!="CAND-003":raise ProofEngineError("reserve or held candidate changed")
 if any(v[x] is not None for x in ("selected_candidate","named_recipient","contact_channel","personalized_message")):raise ProofEngineError("contact target silently populated")
 if tuple(v[x] for x in ("contact_event_count","customer_intake_event_count","pilot_execution_event_count"))!=(0,0,0):raise ProofEngineError("external action count changed")
 if v["next_gate"]!="HUMAN_RECOMMENDED_CANDIDATE_SELECTION_AND_CONTACT_AUTHORIZATION_REQUIRED":raise ProofEngineError("next human gate changed")
 _c(v["authority"]);return v
def verify_risk(v=None):
 v=_s("risk",v,"risk_review_fingerprint")
 if (v["contract_fingerprint"],v["decision_fingerprint"],v["prior_outreach_template_fingerprint"])!=(FP["contract"],FP["decision"],"ffd966240ad007c2842198b65686db381e760e436b0d2852bea760015056e88a"):raise ProofEngineError("risk review binding mismatch")
 if v["contact_status"]!="NOT_AUTHORIZED_NOT_PERFORMED" or v["contact_event_count"]!=0:raise ProofEngineError("contact already authorized or performed")
 if (len(v["recommended_candidate_risks"]),len(v["reserve_candidate_risks"]),len(v["prohibited_actions"]))!=(5,2,7):raise ProofEngineError("prohibited action or risk set weakened")
 if v["external_action_performed"] is not False:raise ProofEngineError("external action recorded")
 _c(v["authority"]);return v
def verify_score_hold(v=None):
 v=_s("score_hold",v,"score_hold_fingerprint")
 if tuple(v[x] for x in ("contract_fingerprint","decision_fingerprint","risk_review_fingerprint"))!=(FP["contract"],FP["decision"],FP["risk"]):raise ProofEngineError("score hold binding mismatch")
 if tuple(v[x] for x in ("product_readiness_score_before","product_readiness_score_after","score_change","rts_overall_planning_estimate_percent_before","rts_overall_planning_estimate_percent_after"))!=(93,93,0,78,79):raise ProofEngineError("readiness or planning score changed")
 if len(v["reasons_for_readiness_hold"])!=3 or len(v["not_supported"])!=6:raise ProofEngineError("score hold reasoning weakened")
 _c(v["authority"]);return v
def verify_completion(v=None):
 v=_s("completion",v,"completion_fingerprint");e={"candidate_universe":FP["universe"],"evidence_snapshot":FP["evidence"],"candidate_scores":FP["scores"],"shortlist_decision":FP["decision"],"contact_risk_review":FP["risk"],"score_hold":FP["score_hold"]}
 if v["contract_fingerprint"]!=FP["contract"] or v["artifact_fingerprints"]!=e:raise ProofEngineError("completion binding mismatch")
 if (v["state"],v["next_gate"])!=("INTERNAL_PUBLIC_CANDIDATE_SHORTLIST_COMPLETE","HUMAN_RECOMMENDED_CANDIDATE_SELECTION_AND_CONTACT_AUTHORIZATION_REQUIRED"):raise ProofEngineError("completion state mismatch")
 if tuple(v[x] for x in ("candidate_count","shortlist_count","recommended_count","selected_count","contact_event_count","customer_intake_event_count","pilot_execution_event_count","product_readiness_score","rts_overall_planning_estimate_percent"))!=(3,2,1,0,0,0,0,93,79):raise ProofEngineError("completion count mismatch")
 if len(v["acceptance_results"])!=10 or any(x["result"]!="PASS" for x in v["acceptance_results"]):raise ProofEngineError("completion acceptance mismatch")
 _c(v["authority"]);return v
def verify_progress(v=None):
 v=_s("status",v,"map_fingerprint");a=v["final_shape"]["axes"];c=v["current_position"]
 if (sum(x["score"] for x in a),sum(x["maximum"] for x in a))!=(79,100):raise ProofEngineError("progress score mismatch")
 if tuple(c[x] for x in ("current_state","next_gate","rts_overall_planning_estimate_percent","short_term_internal_hardening_percent","product_readiness_score","candidate_count","shortlist_count","recommended_candidate_repository"))!=("INTERNAL_PUBLIC_CANDIDATE_SHORTLIST_COMPLETE","HUMAN_RECOMMENDED_CANDIDATE_SELECTION_AND_CONTACT_AUTHORIZATION_REQUIRED",79,100,93,3,2,"jbexta/AgentPilot"):raise ProofEngineError("current position mismatch")
 if any(c[x] is not False for x in ("recommended_candidate_selected","real_participant_selected","participant_contact_authorized","participant_contact_performed","customer_intake_authorized","pilot_execution_authorized")):raise ProofEngineError("current position silently widened")
 _c(v["authority"]);return v
def verify_checkpoint(v=None):
 v=_s("checkpoint",v,"checkpoint_fingerprint");e={"candidate_discovery_contract_fingerprint":"contract","candidate_universe_fingerprint":"universe","candidate_evidence_snapshot_fingerprint":"evidence","candidate_scores_fingerprint":"scores","shortlist_decision_fingerprint":"decision","contact_risk_review_fingerprint":"risk","score_hold_fingerprint":"score_hold","completion_fingerprint":"completion","progress_map_fingerprint":"status"}
 if any(v[f]!=FP[k] for f,k in e.items()):raise ProofEngineError("checkpoint artifact binding mismatch")
 if (v["prior_execution_authorization_status_fingerprint"],v["prior_execution_authorization_checkpoint_fingerprint"])!=(PRIOR_STATUS_FP,PRIOR_CHECKPOINT_FP):raise ProofEngineError("checkpoint history binding mismatch")
 if tuple(v[x] for x in ("candidate_count","shortlist_count","recommended_count","selected_count","product_readiness_score","rts_overall_planning_estimate_percent","short_term_internal_hardening_percent"))!=(3,2,1,0,93,79,100):raise ProofEngineError("checkpoint values mismatch")
 if any(v[x] is not False for x in v if x.endswith("_performed")):raise ProofEngineError("checkpoint external action recorded")
 return v
def verify_candidate_shortlist_stage():
 r={"history":verify_prior_execution_authorization_history(),"contract":verify_contract(),"universe":verify_universe(),"evidence":verify_evidence(),"scores":verify_scores(),"decision":verify_decision(),"risk":verify_risk(),"score_hold":verify_score_hold(),"completion":verify_completion(),"progress":verify_progress(),"checkpoint":verify_checkpoint()}
 r["summary"]={"state":"INTERNAL_PUBLIC_CANDIDATE_SHORTLIST_COMPLETE","next_gate":"HUMAN_RECOMMENDED_CANDIDATE_SELECTION_AND_CONTACT_AUTHORIZATION_REQUIRED","rts_overall_planning_estimate_percent":79,"short_term_internal_hardening_percent":100,"product_readiness_score":93,"product_readiness_score_change":0,"candidate_count":3,"shortlist_count":2,"recommended_candidate_repository":"jbexta/AgentPilot","recommended_candidate_score":86,"reserve_candidate_repository":"tmseidel/ai-git-bot","reserve_candidate_score":83,"selected_candidate_count":0,"participant_contact_authorized":False,"participant_contact_performed":False,"customer_intake_authorized":False,"pilot_execution_authorized":False,"external_actions_performed":False}
 return r
