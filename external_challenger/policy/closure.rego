package external_challenger.closure

import rego.v1

# This policy deliberately contains no RTS runtime code and no persistent state.
# Cryptographic verification, workload attestation, runtime discovery, tracing,
# WORM retention and human approval are delegated to external tools. Rego only
# binds their verified outputs into fail-closed lifecycle decisions.

default allow_execution := false

default allow_outcome := false

default allow_promotion := false

default allow_governance_change := false

default allow_full_cycle := false

scope_authorized if {
	some i
	input.authority.allowed_surfaces[i] == input.authority.requested_surface
}

allow_execution if {
	input.entrypoint == "proof-closure"
	input.claim.supported_by_evidence
	scope_authorized
	input.deployment.source_revision == input.expected.source_revision
	input.deployment.artifact_digest == input.expected.artifact_digest
	input.deployment.config_digest == input.expected.config_digest
	input.deployment.environment_digest == input.expected.environment_digest
	input.deployment.workload_attested
	input.deployment.route_set_verified
	input.deployment.process_identity_verified
	input.deployment.instance_artifact_coverage_verified
	input.deployment.collector_policy_bound
	input.deployment.collector_independence_verified
	input.deployment.fresh
	input.deployment.material_match_verified
	input.deployment.authorization_granted
	input.runtime.deployment_fingerprint == input.deployment.fingerprint
	input.runtime.expectation_fingerprint == input.expected.fingerprint
	input.runtime.session_id != ""
	input.runtime.execution_id != ""
	input.runtime.trace_id != ""
}

allow_outcome if {
	allow_execution
	input.outcome.signature_verified
	input.outcome.source_trusted
	not input.outcome.replayed
	input.outcome.evidence_id != ""
	input.outcome.deployment_fingerprint == input.deployment.fingerprint
	input.outcome.expectation_fingerprint == input.expected.fingerprint
	input.outcome.session_id == input.runtime.session_id
	input.outcome.execution_id == input.runtime.execution_id
	input.outcome.runtime_fingerprint == input.runtime.fingerprint
	input.outcome.within_execution_window
	input.outcome.retained_worm
	input.retention.all_terminal_paths_captured
	input.retention.worm_policy_enforced
	input.outcome.classification in {"SUCCESS", "FAILURE", "ESCALATION", "RECOVERY", "REJECTED", "WITHHELD"}
}

allow_promotion if {
	allow_outcome
	input.promotion.entrypoint == "proof-closure"
	input.learning.proposal_present
	input.learning.regression_passed
	input.learning.counter_evidence_checked
	input.learning.rollback_material_present
	input.learning.independent_promotion_approved
	not input.learning.approver_is_proposer
	input.learning.capability_digest != ""
	input.learning.capability_digest == input.promotion.authorized_capability_digest
	input.promotion.protected_environment
	input.promotion.no_admin_bypass
	input.promotion.changed_capability_reenters_proof_chain
}

allow_governance_change if {
	input.governance.entrypoint == "proof-closure"
	input.governance.change_requested
	input.governance.policy_source_protected
	input.governance.required_checks_passed
	input.governance.independent_review
	not input.governance.self_exempt
	input.governance.signed_policy_artifact
	input.governance.new_policy_reenters_same_gate
}

allow_full_cycle if {
	allow_execution
	allow_outcome
	allow_promotion
	allow_governance_change
}
