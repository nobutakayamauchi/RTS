from __future__ import annotations

import unittest

from deployment_identity.attestation import AttestationError, compute_hmac_signature, establish_attested_deployment_identity
from deployment_identity.core import BOUND, NOT_BOUND, bind_runtime_observation, fingerprint_expectation, fingerprint_observation
from deployment_identity.provenance import ProvenanceError, compute_provenance_signature


class DeploymentIdentityTests(unittest.TestCase):
    def expectation(self):
        return {"source_revision":"abc123","artifact_digest":"sha256:artifact-good","config_fingerprint":"sha256:config-good","environment_fingerprint":"sha256:env-good"}

    def observation(self):
        return {
            "service_unit":"svc","working_directory":"/srv/app","executable_or_module":"python -m app",
            "active_route_surface":"POST /render","deployed_revision":"abc123","deployed_artifact_digest":"sha256:artifact-good",
            "runtime_config_fingerprint":"sha256:config-good","runtime_environment_fingerprint":"sha256:env-good","source_tree_state":"CLEAN",
            "runtime_instances":[{"instance_id":"worker-1","revision":"abc123","artifact_digest":"sha256:artifact-good","config_fingerprint":"sha256:config-good","environment_fingerprint":"sha256:env-good"}],
            "active_route_instance_ids":["worker-1"],"observer_id":"observer-prod-01","observation_session_id":"session-001","observed_at":"2026-08-09T17:00:00+09:00",
        }

    def attestor_keys(self): return {"attestor-a":"a","attestor-b":"b"}
    def collector_keys(self): return {"collector-a":"ca","collector-b":"cb","collector-c":"cc"}
    def collector_domains(self): return {"collector-a":"host-plane","collector-b":"network-plane","collector-c":"aux-plane"}

    def attestations(self, observation=None, expectation=None):
        observation=observation or self.observation(); expectation=expectation or self.expectation(); out=[]
        for aid in ("attestor-a","attestor-b"):
            m={"attestor_id":aid,"observation_fingerprint":fingerprint_observation(observation),"expectation_fingerprint":fingerprint_expectation(expectation),"observation_session_id":observation["observation_session_id"],"issued_at":"2026-08-09T17:00:05+09:00"}
            out.append({**m,"signature":compute_hmac_signature(m,self.attestor_keys()[aid])})
        return out

    def provenance(self, observation=None, expectation=None, same_domain=False):
        observation=observation or self.observation(); expectation=expectation or self.expectation(); records=[]
        domains=("host-plane","network-plane") if not same_domain else ("host-plane","host-plane")
        route_value=",".join(sorted(observation["active_route_instance_ids"]))
        for collector,domain in zip(("collector-a","collector-b"),domains):
            for stage,subject,value in (
                ("route",observation["active_route_surface"],route_value),("process","svc",observation["executable_or_module"]),("instance","worker-1","worker-1"),("artifact","worker-1","sha256:artifact-good"),
            ):
                m={"record_id":f"{collector}-{stage}","collector_id":collector,"trust_domain":domain,"source_locator":f"{domain}:{stage}","measurement_stage":stage,"subject_id":subject,"observed_value":value,"observation_fingerprint":fingerprint_observation(observation),"expectation_fingerprint":fingerprint_expectation(expectation),"observation_session_id":observation["observation_session_id"],"issued_at":"2026-08-09T17:00:06+09:00"}
                records.append({**m,"signature":compute_provenance_signature(m,self.collector_keys()[collector])})
        return records

    def establish(self, **kwargs):
        o=kwargs.get("observation",self.observation()); e=kwargs.get("expectation",self.expectation())
        return establish_attested_deployment_identity(o,expected_deployment=e,trusted_observer_ids=["observer-prod-01"],reference_time="2026-08-09T17:00:10+09:00",attestations=kwargs.get("attestations",self.attestations(o,e)),trusted_attestation_keys=self.attestor_keys(),collector_provenance=kwargs.get("collector_provenance",self.provenance(o,e)),trusted_collector_keys=self.collector_keys(),trusted_collector_domains=kwargs.get("trusted_collector_domains",self.collector_domains()),max_age_seconds=300,min_attestors=2,min_independent_domains=2)

    def resign(self, record):
        material={k:v for k,v in record.items() if k!="signature"}; record["signature"]=compute_provenance_signature(material,self.collector_keys()[record["collector_id"]])

    def add_instance_record(self, records, collector, domain, instance_id, observation):
        m={"record_id":f"{collector}-instance-{instance_id}","collector_id":collector,"trust_domain":domain,"source_locator":f"{domain}:instance:{instance_id}","measurement_stage":"instance","subject_id":instance_id,"observed_value":instance_id,"observation_fingerprint":fingerprint_observation(observation),"expectation_fingerprint":fingerprint_expectation(self.expectation()),"observation_session_id":observation["observation_session_id"],"issued_at":"2026-08-09T17:00:06+09:00"}
        records.append({**m,"signature":compute_provenance_signature(m,self.collector_keys()[collector])})

    def test_independent_provenance_authorizes(self):
        proof=self.establish(); self.assertTrue(proof["runtime_classification_authorized"]); self.assertEqual(proof["collector_provenance"]["verified_trust_domains"],["host-plane","network-plane"])

    def test_attestation_quorum_without_provenance_cannot_authorize(self):
        with self.assertRaisesRegex(ProvenanceError,"non-empty array"): self.establish(collector_provenance=[])

    def test_claimed_domain_cannot_override_external_policy(self):
        p=self.provenance(same_domain=True)
        with self.assertRaisesRegex(ProvenanceError,"policy binds network-plane"): self.establish(collector_provenance=p)

    def test_missing_external_domain_binding_fails(self):
        with self.assertRaisesRegex(ProvenanceError,"no externally trusted domain binding"): self.establish(trusted_collector_domains={"collector-a":"host-plane"})

    def test_shared_source_locator_cannot_fake_independence(self):
        p=self.provenance(); a=next(r for r in p if r["collector_id"]=="collector-a" and r["measurement_stage"]=="route"); b=next(r for r in p if r["collector_id"]=="collector-b" and r["measurement_stage"]=="route"); b["source_locator"]=a["source_locator"]; self.resign(b)
        with self.assertRaisesRegex(ProvenanceError,"shared across trust domains"): self.establish(collector_provenance=p)

    def test_missing_stage_in_one_domain_fails_closed(self):
        p=[r for r in self.provenance() if not (r["trust_domain"]=="network-plane" and r["measurement_stage"]=="process")]
        with self.assertRaisesRegex(ProvenanceError,"missing measurement stages"): self.establish(collector_provenance=p)

    def test_every_domain_must_cover_every_routed_instance(self):
        o=self.observation(); second=dict(o["runtime_instances"][0]); second["instance_id"]="worker-2"; o["runtime_instances"].append(second); o["active_route_instance_ids"]=["worker-1","worker-2"]
        p=self.provenance(o,self.expectation())
        with self.assertRaisesRegex(ProvenanceError,"every routed instance"): self.establish(observation=o,collector_provenance=p,attestations=self.attestations(o,self.expectation()))

    def test_every_domain_must_measure_artifact_for_every_routed_instance(self):
        o=self.observation(); second=dict(o["runtime_instances"][0]); second["instance_id"]="worker-2"; o["runtime_instances"].append(second); o["active_route_instance_ids"]=["worker-1","worker-2"]
        p=self.provenance(o,self.expectation())
        self.add_instance_record(p,"collector-a","host-plane","worker-2",o); self.add_instance_record(p,"collector-b","network-plane","worker-2",o)
        with self.assertRaisesRegex(ProvenanceError,"artifact for every routed instance"): self.establish(observation=o,collector_provenance=p,attestations=self.attestations(o,self.expectation()))

    def test_artifact_measurement_mismatch_fails(self):
        p=self.provenance(); target=next(r for r in p if r["collector_id"]=="collector-b" and r["measurement_stage"]=="artifact"); target["observed_value"]="sha256:evil"; self.resign(target)
        with self.assertRaisesRegex(ProvenanceError,"artifact measurement mismatch"): self.establish(collector_provenance=p)

    def test_route_and_process_values_are_measured(self):
        for stage,bad,pattern in (("route","wrong-worker","route measurement mismatch"),("process","wrong-process","process measurement mismatch")):
            p=self.provenance(); target=next(r for r in p if r["collector_id"]=="collector-b" and r["measurement_stage"]==stage); target["observed_value"]=bad; self.resign(target)
            with self.assertRaisesRegex(ProvenanceError,pattern): self.establish(collector_provenance=p)

    def test_forged_provenance_signature_fails(self):
        p=self.provenance(); p[0]["signature"]="0"*64
        with self.assertRaisesRegex(ProvenanceError,"invalid provenance signature"): self.establish(collector_provenance=p)

    def test_provenance_from_different_session_fails(self):
        p=self.provenance(); p[0]["observation_session_id"]="other"; self.resign(p[0])
        with self.assertRaisesRegex(ProvenanceError,"different session"): self.establish(collector_provenance=p)

    def test_attestor_quorum_still_required(self):
        with self.assertRaisesRegex(AttestationError,"quorum not met"): self.establish(attestations=self.attestations()[:1])

    def test_runtime_binding_requires_fully_authorized_proof(self):
        proof=self.establish(); runtime={"deployment_identity_fingerprint":proof["observation_fingerprint"],"deployment_expectation_fingerprint":proof["expectation_fingerprint"],"observation_session_id":"session-001","observed_at":"2026-08-09T17:00:15+09:00","result":{"status":"ok"}}
        bound=bind_runtime_observation(proof,runtime); self.assertEqual(bound["status"],BOUND)
        runtime["observation_session_id"]="other"; self.assertEqual(bind_runtime_observation(proof,runtime)["status"],NOT_BOUND)


if __name__ == "__main__": unittest.main()
