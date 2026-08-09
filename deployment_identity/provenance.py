from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


class ProvenanceError(ValueError):
    """Raised when measured collector provenance cannot establish independent paths."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _parse_timestamp(value: str, field: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ProvenanceError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ProvenanceError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def provenance_material(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "signature"}


def compute_provenance_signature(material: Mapping[str, Any], secret: str) -> str:
    if not isinstance(secret, str) or not secret:
        raise ProvenanceError("collector secret must be a non-empty string")
    return hmac.new(secret.encode("utf-8"), _canonical_json(dict(material)).encode("utf-8"), hashlib.sha256).hexdigest()


def verify_collector_provenance(
    records: Sequence[Mapping[str, Any]],
    *,
    trusted_collector_keys: Mapping[str, str],
    observation_fingerprint: str,
    expectation_fingerprint: str,
    observation_session_id: str,
    active_route_instance_ids: Sequence[str],
    expected_artifact_digest: str,
    reference_time: str,
    max_age_seconds: int = 300,
    min_independent_domains: int = 2,
) -> dict[str, Any]:
    """Verify signed, independently sourced route/process/instance/artifact provenance.

    Each trust domain must independently cover the same four measurement stages:
    route -> process -> instance -> artifact. Records bind the exact deployment
    observation, expectation and session. This validates provenance diversity and
    consistency; it does not prove a jointly compromised substrate cannot lie.
    """
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)) or not records:
        raise ProvenanceError("collector provenance must be a non-empty array")
    if not isinstance(trusted_collector_keys, Mapping) or not trusted_collector_keys:
        raise ProvenanceError("trusted_collector_keys must be a non-empty mapping")
    if not isinstance(min_independent_domains, int) or min_independent_domains < 2:
        raise ProvenanceError("min_independent_domains must be at least 2")
    if not isinstance(max_age_seconds, int) or max_age_seconds < 0:
        raise ProvenanceError("max_age_seconds must be a non-negative integer")

    required_stages = {"route", "process", "instance", "artifact"}
    expected_instances = set(active_route_instance_ids)
    if not expected_instances:
        raise ProvenanceError("active_route_instance_ids must be non-empty")

    reference = _parse_timestamp(reference_time, "reference_time")
    seen_record_ids: set[str] = set()
    collector_domains: dict[str, set[str]] = {}
    domain_stages: dict[str, set[str]] = {}
    domain_instances: dict[str, set[str]] = {}
    verified_records: list[str] = []

    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise ProvenanceError(f"collector_provenance[{index}] must be an object")
        required = (
            "record_id",
            "collector_id",
            "trust_domain",
            "source_locator",
            "measurement_stage",
            "subject_id",
            "observed_value",
            "observation_fingerprint",
            "expectation_fingerprint",
            "observation_session_id",
            "issued_at",
            "signature",
        )
        values: dict[str, str] = {}
        for field in required:
            value = record.get(field)
            if not isinstance(value, str) or not value or value != value.strip():
                raise ProvenanceError(f"collector_provenance[{index}].{field} must be an exact non-empty string")
            values[field] = value

        record_id = values["record_id"]
        if record_id in seen_record_ids:
            raise ProvenanceError(f"duplicate provenance record_id: {record_id}")
        seen_record_ids.add(record_id)

        collector_id = values["collector_id"]
        secret = trusted_collector_keys.get(collector_id)
        if not isinstance(secret, str) or not secret:
            raise ProvenanceError(f"untrusted collector_id: {collector_id}")
        if values["observation_fingerprint"] != observation_fingerprint:
            raise ProvenanceError(f"collector {collector_id} measured a different observation")
        if values["expectation_fingerprint"] != expectation_fingerprint:
            raise ProvenanceError(f"collector {collector_id} measured a different expectation")
        if values["observation_session_id"] != observation_session_id:
            raise ProvenanceError(f"collector {collector_id} measured a different session")

        stage = values["measurement_stage"]
        if stage not in required_stages:
            raise ProvenanceError(f"unsupported measurement_stage: {stage}")

        issued = _parse_timestamp(values["issued_at"], f"collector_provenance[{index}].issued_at")
        age = (reference - issued).total_seconds()
        if age < 0 or age > max_age_seconds:
            raise ProvenanceError(f"collector {collector_id} provenance is stale or future-dated")

        expected_signature = compute_provenance_signature(provenance_material(record), secret)
        if not hmac.compare_digest(values["signature"], expected_signature):
            raise ProvenanceError(f"invalid provenance signature for collector_id: {collector_id}")

        domain = values["trust_domain"]
        collector_domains.setdefault(domain, set()).add(collector_id)
        domain_stages.setdefault(domain, set()).add(stage)

        if stage == "instance":
            if values["subject_id"] not in expected_instances:
                raise ProvenanceError(f"collector {collector_id} referenced non-routed instance: {values['subject_id']}")
            domain_instances.setdefault(domain, set()).add(values["subject_id"])
        elif stage == "artifact":
            if values["observed_value"] != expected_artifact_digest:
                raise ProvenanceError(f"collector {collector_id} artifact measurement mismatch")

        verified_records.append(record_id)

    if len(domain_stages) < min_independent_domains:
        raise ProvenanceError(
            f"independent provenance domain quorum not met: {len(domain_stages)} < {min_independent_domains}"
        )

    for domain, stages in domain_stages.items():
        missing = required_stages - stages
        if missing:
            raise ProvenanceError(f"trust domain {domain} missing measurement stages: {sorted(missing)}")
        if domain_instances.get(domain, set()) != expected_instances:
            raise ProvenanceError(f"trust domain {domain} did not independently cover every routed instance")

    return {
        "status": "COLLECTOR_PROVENANCE_VERIFIED",
        "verified_record_ids": sorted(verified_records),
        "verified_trust_domains": sorted(domain_stages),
        "independent_domain_count": len(domain_stages),
        "min_independent_domains": min_independent_domains,
    }
