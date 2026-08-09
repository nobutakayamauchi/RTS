package external_challenger.overtime

import rego.v1

default allow_learning := false
default allow_regression := false
default allow_promotion := false
default allow_deploy := false
default allow_runtime := false
default allow_new_outcome := false
default allow_recovery := false
default allow_policy_activation := false
default allow_policy_rollback := false
default allow_provider_transition := false

exact_roles if {
  input.roles.proposer != ""
  input.roles.evaluator != ""
  input.roles.promoter != ""
  input.roles.proposer != input.roles.evaluator
  input.roles.proposer != input.roles.promoter
  input.roles.evaluator != input.roles.promoter
}

allow_policy_activation if {
  input.kind == "policy_activation"
  input.policy.provenance_verified
  input.policy.activation_attestation_verified
  input.policy.authority_identity == input.expected.policy_authority_identity
  input.policy.version == input.expected.policy_version
  input.policy.digest == input.expected.policy_digest
  input.policy.source_revision == input.expected.source_revision
  input.policy.run_id == input.expected.run_id
  input.policy.status == "ACTIVE"
}

allow_policy_rollback if {
  input.kind == "policy_rollback"
  input.policy.activation_attestation_verified
  input.policy.authority_identity == input.expected.policy_authority_identity
  input.policy.rollback_digest == input.expected.rollback_digest
  input.policy.run_id == input.expected.run_id
  input.policy.rollback_authorized
}

allow_learning if {
  input.kind == "learning"
  input.policy_verified
  input.outcome.verified
  input.outcome.classification == "FAILURE"
  input.outcome.execution_id == input.expected.execution_id
  input.outcome.capability_digest == input.expected.capability_digest
  input.outcome.run_id == input.expected.run_id
  input.proposal.verified
  input.proposal.proposer_identity == input.expected.proposer_identity
  input.proposal.source_outcome_digest == input.expected.outcome_digest
  input.proposal.current_capability_digest == input.expected.capability_digest
  input.proposal.run_id == input.expected.run_id
}

allow_regression if {
  input.kind == "regression"
  input.policy_verified
  input.proposal.verified
  input.proposal.proposer_identity == input.expected.proposer_identity
  input.proposal.run_id == input.expected.run_id
  input.dataset.verified
  input.dataset.version == input.expected.dataset_version
  input.dataset.source_outcome_digest == input.expected.outcome_digest
  input.dataset.proposal_digest == input.expected.proposal_digest
  input.regression.verified
  input.regression.status == "PASS"
  input.regression.fail_count == 0
  input.regression.candidate_digest == input.expected.candidate_digest
  input.regression.dataset_digest == input.expected.dataset_digest
  input.regression.proposal_digest == input.expected.proposal_digest
  input.regression.run_id == input.expected.run_id
}

allow_promotion if {
  input.kind == "promotion"
  input.policy_verified
  exact_roles
  input.roles.proposer == input.expected.proposer_identity
  input.roles.evaluator == input.expected.evaluator_identity
  input.roles.promoter == input.expected.promoter_identity
  input.proposal_verified
  input.regression_verified
  input.regression_status == "PASS"
  input.regression_run_id == input.expected.run_id
  input.candidate_verified
  input.candidate_digest == input.expected.candidate_digest
  input.proposal_digest == input.expected.proposal_digest
  input.regression_digest == input.expected.regression_digest
  input.approval_run_id == input.expected.run_id
}

allow_deploy if {
  input.kind == "deploy"
  input.policy_verified
  input.promotion_verified
  input.promotion.decision == "APPROVED"
  input.promotion.authority_identity == input.expected.promoter_identity
  input.promotion.run_id == input.expected.run_id
  input.promotion.authorized_capability_digest == input.expected.candidate_digest
  input.promotion.proposal_digest == input.expected.proposal_digest
  input.promotion.regression_digest == input.expected.regression_digest
  input.candidate_verified
  input.candidate_digest == input.expected.candidate_digest
  input.candidate_source_revision == input.expected.source_revision
}

allow_runtime if {
  input.kind == "runtime"
  input.policy_verified
  input.runtime.evidence_available
  input.runtime.endpoint_fresh
  input.runtime.expected_digest == input.expected.candidate_digest
  input.runtime.config_digest == input.expected.candidate_digest
  input.runtime.routed_pod_count > 0
  input.runtime.routed_pod_count == input.runtime.expected_pod_count
  input.runtime.all_routed_pods_ready
  input.runtime.all_routed_pods_match_digest
  input.runtime.old_digest_routed == false
  input.runtime.active_route_digest == input.expected.candidate_digest
}

allow_new_outcome if {
  input.kind == "new_outcome"
  input.policy_verified
  input.outcome.verified
  input.outcome.classification == "SUCCESS"
  input.outcome.run_id == input.expected.run_id
  input.outcome.execution_id == input.expected.execution_id
  input.outcome.capability_digest == input.expected.candidate_digest
  input.outcome.runtime_route_fingerprint == input.expected.runtime_route_fingerprint
  input.outcome.promotion_digest == input.expected.promotion_digest
}

allow_recovery if {
  input.kind == "recovery"
  input.policy_verified
  input.promotion_verified
  input.recovery.evidence_available
  input.recovery.authority_bound
  input.recovery.promotion_digest == input.expected.promotion_digest
  input.recovery.from_capability_digest == input.expected.candidate_digest
  input.recovery.rollback_digest == input.expected.rollback_digest
  input.recovery.active_route_digest == input.expected.rollback_digest
  input.recovery.run_id == input.expected.run_id
}

allow_provider_transition if {
  input.kind == "provider_transition"
  input.providers.evidence_api_available
  input.providers.retention_available
  input.providers.approval_available
  input.providers.policy_available
  input.providers.runtime_credentials_available
}
