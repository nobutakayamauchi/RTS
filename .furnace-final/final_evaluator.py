from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import pathlib
import subprocess
import sys
from typing import Any

from datasets import disable_progress_bars, load_dataset


DATASET_REPO = "SWE-bench-Live/MultiLang"
DATASET_REVISION = "608f7ae9ab8ea1f9f0d030fe04562cf6bd1a0c8b"
EVALUATOR_REVISION = "70ec57e852e3f2d195790fe71f553e272c691833"
SEED_SHA256 = "050b40668443f667bcc5eabb7ff6c0ea3db5f2e962ac2178ce8e95d4e9e7921b"
FINAL_SCHEMA = "ultimate-loop-reconstruction-furnace/final-eval-v1"


class FinalEvalError(RuntimeError):
    pass


def _candidate_order(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    ranked: list[tuple[str, dict[str, Any]]] = []
    for row in rows:
        instance_id = row.get("instance_id")
        if not isinstance(instance_id, str) or not instance_id:
            raise FinalEvalError("validator-side instance identity missing")
        digest = hashlib.sha256(
            f"{SEED_SHA256}|{split}|{instance_id}".encode("utf-8")
        ).hexdigest()
        ranked.append((digest, row))
    ranked.sort(key=lambda item: item[0])
    return [row for _, row in ranked]


def _load_frozen_request(path: pathlib.Path) -> dict[str, Any]:
    request = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "task_id", "split", "candidate_rank", "patch", "commands"}
    if not isinstance(request, dict) or set(request) != required:
        raise FinalEvalError("frozen request shape drift")
    if request["schema_version"] != "ultimate-loop-reconstruction-furnace/solver-request-v1":
        raise FinalEvalError("frozen request schema mismatch")
    if request["split"] != "go" or request["candidate_rank"] != 1:
        raise FinalEvalError("final evaluation is frozen to Stage 0 Go rank 1")
    if request["task_id"] != "FURNACE-02-6F812634AF9D173B":
        raise FinalEvalError("opaque task identity drift")
    if not isinstance(request["patch"], str) or not request["patch"].strip():
        raise FinalEvalError("candidate patch missing")
    return request


def run(
    *,
    evaluator_root: pathlib.Path,
    request_path: pathlib.Path,
    private_root: pathlib.Path,
    safe_output: pathlib.Path,
) -> int:
    request = _load_frozen_request(request_path)
    disable_progress_bars()
    rows = [dict(row) for row in load_dataset(DATASET_REPO, split="go", revision=DATASET_REVISION)]
    ordered = _candidate_order(rows, "go")
    row = ordered[0]

    private_root.mkdir(parents=True, exist_ok=True)
    dataset_path = private_root / "candidate.jsonl"
    predictions_path = private_root / "predictions.json"
    output_dir = private_root / "official-evaluation"
    private_log = private_root / "official-evaluator-private.log"

    dataset_path.write_text(
        json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    predictions_path.write_text(
        json.dumps(
            {row["instance_id"]: {"model_patch": request["patch"]}},
            sort_keys=True,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    command = [
        sys.executable,
        "evaluation/evaluation.py",
        "--dataset",
        str(dataset_path.resolve()),
        "--patch_dir",
        str(predictions_path.resolve()),
        "--platform",
        "linux",
        "--workers",
        "1",
        "--output_dir",
        str(output_dir.resolve()),
        "--overwrite",
        "1",
    ]

    with private_log.open("wb") as log:
        proc = subprocess.run(
            command,
            cwd=evaluator_root,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=170 * 60,
        )

    results_path = output_dir / "results.json"
    aggregate: dict[str, Any] = {}
    if results_path.exists():
        try:
            aggregate = json.loads(results_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            aggregate = {}

    success = int(aggregate.get("success", 0) or 0)
    failure = int(aggregate.get("failure", 0) or 0)
    error = int(aggregate.get("error", 0) or 0)
    incomplete = int(aggregate.get("incomplete", 0) or 0)
    empty_patch = int(aggregate.get("empty_patch", 0) or 0)
    submitted = int(aggregate.get("submitted", 0) or 0)

    if proc.returncode != 0 or error or incomplete or submitted != 1:
        state = "ERROR"
        exit_code = 2
    elif success == 1 and failure == 0 and empty_patch == 0:
        state = "PASS"
        exit_code = 0
    elif failure == 1 and success == 0:
        state = "FAIL"
        exit_code = 1
    else:
        state = "ERROR"
        exit_code = 2

    safe = {
        "schema_version": FINAL_SCHEMA,
        "task_id": request["task_id"],
        "split": "go",
        "candidate_rank": 1,
        "dataset_revision": DATASET_REVISION,
        "evaluator_revision": EVALUATOR_REVISION,
        "state": state,
        "submitted": submitted,
        "success": success,
        "failure": failure,
        "error": error,
        "incomplete": incomplete,
        "empty_patch": empty_patch,
        "hidden_test_details_exposed": False,
        "iterative_hidden_tuning_authorized": False,
    }
    safe_output.parent.mkdir(parents=True, exist_ok=True)
    safe_output.write_text(
        json.dumps(safe, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"SAFE_FINAL_EVAL task={request['task_id']} state={state}")
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluator-root", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--private-root", required=True)
    parser.add_argument("--safe-output", required=True)
    args = parser.parse_args()
    return run(
        evaluator_root=pathlib.Path(args.evaluator_root).resolve(),
        request_path=pathlib.Path(args.request).resolve(),
        private_root=pathlib.Path(args.private_root).resolve(),
        safe_output=pathlib.Path(args.safe_output).resolve(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
