package external_challenger.provider_binding

import rego.v1

# Phase 2A consumes GitHub CLI attestation verification output and raw
# Kubernetes API objects. There is no custom collector/controller process.

default allow := false

attested_subject_matches if {
	some result in input.github_attestations
	some subject in result.verificationResult.statement.subject
	subject.digest.sha256 == input.expected.bundle_sha256
}

mounted_bundle_matches if {
	encoded := input.kubernetes.config_map.binaryData["challenger-bundle.tgz"]
	crypto.sha256(base64.decode(encoded)) == input.expected.bundle_sha256
	input.kubernetes.config_map.immutable == true
	input.kubernetes.config_map.data.source_revision == input.expected.source_revision
}

deployment_binds_source if {
	input.kubernetes.deployment.metadata.annotations["challenger.rts/source-revision"] == input.expected.source_revision
	input.kubernetes.deployment.metadata.annotations["challenger.rts/bundle-sha256"] == input.expected.bundle_sha256
	input.kubernetes.deployment.spec.template.metadata.annotations["challenger.rts/source-revision"] == input.expected.source_revision
	input.kubernetes.deployment.spec.template.metadata.annotations["challenger.rts/bundle-sha256"] == input.expected.bundle_sha256
	some volume in input.kubernetes.deployment.spec.template.spec.volumes
	volume.configMap.name == input.kubernetes.config_map.metadata.name
}

routed_pod_names contains name if {
	some slice in input.kubernetes.endpoint_slices.items
	slice.metadata.labels["kubernetes.io/service-name"] == input.expected.service_name
	some endpoint in slice.endpoints
	endpoint.conditions.ready == true
	endpoint.targetRef.kind == "Pod"
	name := endpoint.targetRef.name
}

observed_pod_names contains pod.metadata.name if {
	some pod in input.kubernetes.pods.items
	pod.metadata.labels.app == input.expected.app_label
}

all_routed_pods_observed if {
	count(routed_pod_names) > 0
	routed_pod_names == observed_pod_names
}

pod_is_bound(pod) if {
	pod.status.phase == "Running"
	pod.metadata.annotations["challenger.rts/source-revision"] == input.expected.source_revision
	pod.metadata.annotations["challenger.rts/bundle-sha256"] == input.expected.bundle_sha256
	some volume in pod.spec.volumes
	volume.configMap.name == input.kubernetes.config_map.metadata.name
	every status in pod.status.containerStatuses {
		status.ready == true
		status.containerID != ""
		status.imageID != ""
	}
}

all_routed_pods_runtime_bound if {
	all_routed_pods_observed
	every pod in input.kubernetes.pods.items {
		pod.metadata.name in routed_pod_names
		pod_is_bound(pod)
	}
}

allow if {
	input.verification.github_cli_exit_verified == true
	input.expected.source_revision != ""
	input.expected.bundle_sha256 != ""
	attested_subject_matches
	mounted_bundle_matches
	deployment_binds_source
	all_routed_pods_runtime_bound
}
