package external_challenger.closure

import rego.v1

good_input := {
	"entrypoint": "proof-closure",
	"claim": {"supported_by_evidence": true},
	"authority": {
		"requested_surface": "deploy:agent-capability",
		"allowed_surfaces": ["deploy:agent-capability"]
	},
	"expected": {
		"source_revision": "abc123",
		"artifact_digest": "sha256:artifact",
		"config_digest": "sha256:config",
		"environment_digest": "sha256:env",
		"fingerprint": "expected-fp"
	},
	"deployment": {
		"source_revision": "abc123",
		"artifact_digest": "sha256:artifact",
		"config_digest": "sha256:config",
		"environment_digest": "sha256:env",
		"fingerprint": "deployment-fp",
		"workload_attested": true,
		"route_set_verified": true,
		"process_identity_verified": true,
		"instance_artifact_coverage_verified": true,
		"collector_policy_bound": true,
		"collector_independence_verified": true,
		"fresh": true,
		"material_match_verified": true,
		"authorization_granted": true
	},
	"runtime": {
		"deployment_fingerprint": "deployment-fp",
		"expectation_fingerprint": "expected-fp",
		"fingerprint": "runtime-fp",
		"session_id": "session-001",
		"execution_id": "exec-001",
		"trace_id": "trace-001"
	},
	"outcome": {
		"signature_verified": true,
		"source_trusted": true,
		"replayed": false,
		"evidence_id": "evidence-001",
		"deployment_fingerprint": "deployment-fp",
		"expectation_fingerprint": "expected-fp",
		"session_id": "session-001",
		"execution_id": "exec-001",
		"runtime_fingerprint": "runtime-fp",
		"within_execution_window": true,
		"retained_worm": true,
		"classification": "SUCCESS"
	},
	"retention": {
		"all_terminal_paths_captured": true,
		"worm_policy_enforced": true
	},
	"learning": {
		"proposal_present": true,
		"regression_passed": true,
		"counter_evidence_checked": true,
		"rollback_material_present": true,
		"independent_promotion_approved": true,
		"approver_is_proposer": false,
		"capability_digest": "sha256:capability-v2"
	},
	"promotion": {
		"entrypoint": "proof-closure",
		"authorized_capability_digest": "sha256:capability-v2",
		"protected_environment": true,
		"no_admin_bypass": true,
		"changed_capability_reenters_proof_chain": true
	},
	"governance": {
		"entrypoint": "proof-closure",
		"change_requested": true,
		"policy_source_protected": true,
		"required_checks_passed": true,
		"independent_review": true,
		"self_exempt": false,
		"signed_policy_artifact": true,
		"new_policy_reenters_same_gate": true
	}
}

patch_section(section, patch) := object.union(good_input, {section: object.union(good_input[section], patch)})

test_full_external_cycle_can_be_allowed if {
	allow_full_cycle with input as good_input
}

test_unsupported_claim_is_withheld if {
	bad := patch_section("claim", {"supported_by_evidence": false})
	not allow_execution with input as bad
}

test_second_entrypoint_cannot_bypass_gate if {
	bad := object.union(good_input, {"entrypoint": "manual-api"})
	not allow_execution with input as bad
}

test_scope_does_not_expand_by_implication if {
	bad := object.union(good_input, {"authority": {"requested_surface": "publish:social", "allowed_surfaces": ["deploy:agent-capability"]}})
	not allow_execution with input as bad
}

test_same_revision_different_artifact_is_not_runtime_reality if {
	bad := patch_section("deployment", {"artifact_digest": "sha256:evil"})
	not allow_execution with input as bad
}

test_config_drift_fails if {
	bad := patch_section("deployment", {"config_digest": "sha256:other-config"})
	not allow_execution with input as bad
}

test_unobserved_route_worker_fails if {
	bad := patch_section("deployment", {"route_set_verified": false})
	not allow_execution with input as bad
}

test_self_declared_collector_independence_fails if {
	bad := patch_section("deployment", {"collector_policy_bound": false, "collector_independence_verified": false})
	not allow_execution with input as bad
}

test_stale_deployment_evidence_fails if {
	bad := patch_section("deployment", {"fresh": false})
	not allow_execution with input as bad
}

test_material_match_without_authority_fails if {
	bad := patch_section("deployment", {"material_match_verified": true, "authorization_granted": false})
	not allow_execution with input as bad
}

test_runtime_from_other_deployment_fails if {
	bad := patch_section("runtime", {"deployment_fingerprint": "other-deployment"})
	not allow_execution with input as bad
}

test_outcome_from_other_execution_fails if {
	bad := patch_section("outcome", {"execution_id": "exec-other"})
	not allow_outcome with input as bad
}

test_outcome_from_other_session_fails if {
	bad := patch_section("outcome", {"session_id": "session-other"})
	not allow_outcome with input as bad
}

test_replayed_outcome_fails if {
	bad := patch_section("outcome", {"replayed": true})
	not allow_outcome with input as bad
}

test_forged_outcome_fails if {
	bad := patch_section("outcome", {"signature_verified": false})
	not allow_outcome with input as bad
}

test_failure_is_valid_evidence_when_retained if {
	failure := patch_section("outcome", {"classification": "FAILURE"})
	allow_outcome with input as failure
}

test_failure_cannot_be_discarded if {
	bad := object.union(patch_section("outcome", {"classification": "FAILURE", "retained_worm": false}), {"retention": {"all_terminal_paths_captured": false, "worm_policy_enforced": true}})
	not allow_outcome with input as bad
}

test_success_does_not_imply_promotion if {
	bad := patch_section("learning", {"independent_promotion_approved": false})
	not allow_promotion with input as bad
}

test_proposer_cannot_self_approve_promotion if {
	bad := patch_section("learning", {"approver_is_proposer": true})
	not allow_promotion with input as bad
}

test_regression_failure_blocks_promotion if {
	bad := patch_section("learning", {"regression_passed": false})
	not allow_promotion with input as bad
}

test_promotion_digest_substitution_fails if {
	bad := patch_section("promotion", {"authorized_capability_digest": "sha256:different"})
	not allow_promotion with input as bad
}

test_promotion_bypass_path_fails if {
	bad := patch_section("promotion", {"entrypoint": "direct-deploy"})
	not allow_promotion with input as bad
}

test_changed_capability_must_reenter_chain if {
	bad := patch_section("promotion", {"changed_capability_reenters_proof_chain": false})
	not allow_promotion with input as bad
}

test_governance_cannot_self_exempt if {
	bad := patch_section("governance", {"self_exempt": true})
	not allow_governance_change with input as bad
}

test_governance_change_requires_same_gate if {
	bad := patch_section("governance", {"entrypoint": "admin-direct"})
	not allow_governance_change with input as bad
}

test_new_policy_must_reenter_same_gate if {
	bad := patch_section("governance", {"new_policy_reenters_same_gate": false})
	not allow_governance_change with input as bad
}
