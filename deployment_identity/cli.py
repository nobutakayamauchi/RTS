from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .attestation import AttestationError, establish_attested_deployment_identity
from .core import DeploymentIdentityError, fingerprint_observation


def _read_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeploymentIdentityError(f"cannot read {label}: {path}") from exc
    if not isinstance(value, dict):
        raise DeploymentIdentityError(f"{label} must be a JSON object")
    return value


def _read_array(path: Path, label: str) -> list[dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeploymentIdentityError(f"cannot read {label}: {path}") from exc
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise DeploymentIdentityError(f"{label} must be a JSON array of objects")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RTS Deployment Identity v4")
    sub = parser.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("verify", help="establish attested deployment identity")
    verify.add_argument("--observation", required=True, type=Path)
    verify.add_argument("--expectation", required=True, type=Path)
    verify.add_argument("--attestations", required=True, type=Path)
    verify.add_argument("--attestation-keyring", required=True, type=Path)
    verify.add_argument("--trusted-observer-id", required=True, action="append")
    verify.add_argument("--reference-time", required=True)
    verify.add_argument("--max-age-seconds", type=int, default=300)
    verify.add_argument("--min-attestors", type=int, default=2)

    fingerprint = sub.add_parser("fingerprint", help="fingerprint a deployment observation")
    fingerprint.add_argument("--observation", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        observation = _read_object(args.observation, "observation")
        if args.command == "fingerprint":
            print(fingerprint_observation(observation))
            return 0

        expectation = _read_object(args.expectation, "expectation")
        attestations = _read_array(args.attestations, "attestations")
        keyring = _read_object(args.attestation_keyring, "attestation keyring")
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in keyring.items()):
            raise DeploymentIdentityError("attestation keyring must map string ids to string secrets")

        result = establish_attested_deployment_identity(
            observation,
            expected_deployment=expectation,
            trusted_observer_ids=args.trusted_observer_id,
            reference_time=args.reference_time,
            attestations=attestations,
            trusted_attestation_keys=keyring,
            max_age_seconds=args.max_age_seconds,
            min_attestors=args.min_attestors,
        )
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if result["runtime_classification_authorized"] else 2
    except (DeploymentIdentityError, AttestationError) as exc:
        print(json.dumps({
            "status": "DEPLOYMENT_IDENTITY_NOT_ESTABLISHED",
            "runtime_classification_authorized": False,
            "error": str(exc),
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
