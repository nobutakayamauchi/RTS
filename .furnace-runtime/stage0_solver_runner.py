from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import pathlib
import sys
from typing import Any

from datasets import disable_progress_bars, load_dataset
from launch.core.runtime import SetupRuntime


DATASET_REPO = "SWE-bench-Live/MultiLang"
DATASET_REVISION = "608f7ae9ab8ea1f9f0d030fe04562cf6bd1a0c8b"
SEED_SHA256 = "050b40668443f667bcc5eabb7ff6c0ea3db5f2e962ac2178ce8e95d4e9e7921b"
SUPPORTED = {"c", "go"}
MAX_OUTPUT_BYTES = 200_000


class SolverBridgeError(RuntimeError):
    pass


def _candidate_order(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    decorated: list[tuple[str, dict[str, Any]]] = []
    for row in rows:
        instance_id = row.get("instance_id")
        if not isinstance(instance_id, str) or not instance_id:
            raise SolverBridgeError("validator-side instance identity missing")
        rank = hashlib.sha256(
            f"{SEED_SHA256}|{split}|{instance_id}".encode("utf-8")
        ).hexdigest()
        decorated.append((rank, row))
    decorated.sort(key=lambda item: item[0])
    return [row for _, row in decorated]


def _load_request(path: pathlib.Path) -> dict[str, Any]:
    request = json.loads(path.read_text(encoding="utf-8"))
    expected = {"schema_version", "task_id", "split", "candidate_rank", "patch", "commands"}
    if not isinstance(request, dict) or set(request) != expected:
        raise SolverBridgeError("request shape drift")
    if request["schema_version"] != "ultimate-loop-reconstruction-furnace/solver-request-v1":
        raise SolverBridgeError("request schema mismatch")
    if request["split"] not in SUPPORTED:
        raise SolverBridgeError("unsupported split")
    if not isinstance(request["candidate_rank"], int) or request["candidate_rank"] < 1:
        raise SolverBridgeError("candidate_rank invalid")
    if not isinstance(request["task_id"], str) or not request["task_id"].startswith("FURNACE-"):
        raise SolverBridgeError("opaque task id invalid")
    if not isinstance(request["patch"], str):
        raise SolverBridgeError("patch must be a string")
    commands = request["commands"]
    if (
        not isinstance(commands, list)
        or not 1 <= len(commands) <= 5
        or not all(isinstance(command, str) and command.strip() for command in commands)
    ):
        raise SolverBridgeError("commands invalid")
    return request


def _disconnect_network(container: Any) -> None:
    container.reload()
    networks = dict(container.attrs.get("NetworkSettings", {}).get("Networks", {}))
    client = container.client
    for network_name in networks:
        try:
            client.networks.get(network_name).disconnect(container, force=True)
        except Exception as exc:
            raise SolverBridgeError("failed to enforce offline container") from exc
    container.reload()
    remaining = container.attrs.get("NetworkSettings", {}).get("Networks", {})
    if remaining:
        raise SolverBridgeError("container still has an attached network")


def _redact_output(text: str, row: dict[str, Any]) -> str:
    redacted = text
    unsafe_values = [
        row.get("instance_id"),
        row.get("docker_image"),
        str(row.get("pull_number")) if row.get("pull_number") is not None else None,
    ]
    for value in unsafe_values:
        if isinstance(value, str) and value:
            redacted = redacted.replace(value, "[REDACTED_VALIDATOR_IDENTITY]")
    encoded = redacted.encode("utf-8", errors="replace")
    if len(encoded) > MAX_OUTPUT_BYTES:
        encoded = encoded[:MAX_OUTPUT_BYTES]
        redacted = encoded.decode("utf-8", errors="ignore") + "\n[OUTPUT_TRUNCATED]\n"
    return redacted


def run(request_path: pathlib.Path, output_path: pathlib.Path) -> int:
    request = _load_request(request_path)
    split = request["split"]

    disable_progress_bars()
    dataset = load_dataset(DATASET_REPO, split=split, revision=DATASET_REVISION)
    ordered = _candidate_order([dict(row) for row in dataset], split)
    rank = request["candidate_rank"]
    if rank > len(ordered):
        raise SolverBridgeError("candidate_rank outside split")
    row = ordered[rank - 1]

    private_log = io.StringIO()
    runtime = None
    result: dict[str, Any] = {
        "schema_version": "ultimate-loop-reconstruction-furnace/solver-result-v1",
        "task_id": request["task_id"],
        "split": split,
        "candidate_rank": rank,
        "network_policy": "OFFLINE_AFTER_PREPARE",
        "patch_applied": False,
        "commands": [],
    }

    try:
        with contextlib.redirect_stdout(private_log), contextlib.redirect_stderr(private_log):
            runtime = SetupRuntime.from_launch_image(
                row["docker_image"],
                row["instance_id"],
                platform="linux",
                command_timeout=10,
            )
            _disconnect_network(runtime.container)
            patch = request["patch"]
            if patch:
                if not runtime.apply_patch(patch, verbose=False):
                    result["state"] = "PATCH_APPLY_FAILED"
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                    return 2
                result["patch_applied"] = True

            for command in request["commands"]:
                command_result = runtime.send_command(command)
                exit_code = int(command_result.metadata.exit_code)
                result["commands"].append(
                    {
                        "command": command,
                        "exit_code": exit_code,
                        "output": _redact_output(command_result.output, row),
                    }
                )
                if exit_code != 0:
                    result["state"] = "COMMAND_FAILED"
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                    return 1

            result["state"] = "PASS"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return 0
    finally:
        if runtime is not None:
            try:
                runtime.container.remove(force=True)
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    return run(pathlib.Path(args.request), pathlib.Path(args.output))


if __name__ == "__main__":
    raise SystemExit(main())
