from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
from typing import Any

from datasets import disable_progress_bars, load_dataset

import stage0_control
import task_envelope


DATASET_REPO = "SWE-bench-Live/MultiLang"
DATASET_REVISION = "608f7ae9ab8ea1f9f0d030fe04562cf6bd1a0c8b"
EVALUATOR_REVISION = "70ec57e852e3f2d195790fe71f553e272c691833"
SEED_SHA256 = "050b40668443f667bcc5eabb7ff6c0ea3db5f2e962ac2178ce8e95d4e9e7921b"
SPLIT_ORDINAL = {"c": 1, "go": 2}
SUMMARY_SCHEMA = "ultimate-loop-reconstruction-furnace/validator-summary-v2"


class ValidatorError(RuntimeError):
    pass


def _json_dump(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _evaluate_once(
    *,
    evaluator_root: pathlib.Path,
    candidate_jsonl: pathlib.Path,
    private_root: pathlib.Path,
    candidate_rank: int,
    run_number: int,
) -> bool:
    output_dir = private_root / f"candidate-{candidate_rank:02d}" / f"run-{run_number}"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "validator-private.log"
    command = [
        sys.executable,
        "evaluation/evaluation.py",
        "--dataset",
        str(candidate_jsonl.resolve()),
        "--patch_dir",
        "gold",
        "--platform",
        "linux",
        "--workers",
        "1",
        "--output_dir",
        str(output_dir.resolve()),
        "--overwrite",
        "1",
    ]
    try:
        with log_path.open("wb") as private_log:
            proc = subprocess.run(
                command,
                cwd=evaluator_root,
                stdout=private_log,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=170 * 60,
            )
    except (subprocess.TimeoutExpired, OSError):
        return False
    if proc.returncode != 0:
        return False
    results_path = output_dir / "results.json"
    if not results_path.exists():
        return False
    try:
        results = json.loads(results_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        results.get("submitted") == 1
        and results.get("success") == 1
        and results.get("failure") == 0
        and results.get("error") == 0
        and results.get("incomplete") == 0
        and results.get("empty_patch") == 0
    )


def _initial_summary(split: str, max_candidates: int) -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA,
        "stage": "STAGE0",
        "split": split,
        "state": "VALIDATION_IN_PROGRESS",
        "bounded_prefix_size": max_candidates,
        "candidate_rank": None,
        "gold_validation_runs": 3,
        "gold_validation_passes": None,
        "task_id": None,
        "dataset_revision": DATASET_REVISION,
        "evaluator_revision": EVALUATOR_REVISION,
        "solver_dataset_access": False,
        "solver_gold_access": False,
        "candidate_results": [],
    }


def run(*, split: str, evaluator_root: pathlib.Path, output_root: pathlib.Path, max_candidates: int) -> int:
    if split not in SPLIT_ORDINAL:
        raise ValidatorError("Stage 0 validator accepts only frozen c/go splits")
    if max_candidates < 1:
        raise ValidatorError("max_candidates must be positive")
    if not (evaluator_root / "evaluation" / "evaluation.py").exists():
        raise ValidatorError("pinned evaluator checkout missing")

    private_root = output_root / ".validator-private" / split
    safe_root = output_root / "safe" / split
    private_root.mkdir(parents=True, exist_ok=True)
    safe_root.mkdir(parents=True, exist_ok=True)

    safe_summary = _initial_summary(split, max_candidates)
    _json_dump(safe_root / "validator-summary.json", safe_summary)

    disable_progress_bars()
    dataset = load_dataset(DATASET_REPO, split=split, revision=DATASET_REVISION)
    rows = [dict(row) for row in dataset]
    ordered = stage0_control.candidate_order(rows, split=split, seed_sha256=SEED_SHA256)

    for candidate_rank, row in enumerate(ordered[:max_candidates], 1):
        candidate_file = private_root / f"candidate-{candidate_rank:02d}.jsonl"
        candidate_file.write_text(
            json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        passes = 0
        for run_number in (1, 2, 3):
            if _evaluate_once(
                evaluator_root=evaluator_root,
                candidate_jsonl=candidate_file,
                private_root=private_root,
                candidate_rank=candidate_rank,
                run_number=run_number,
            ):
                passes += 1

        provenance = task_envelope.build_validator_provenance(
            row,
            gold_validation_runs=3,
            gold_validation_passes=passes,
        )
        _json_dump(
            private_root / f"candidate-{candidate_rank:02d}-provenance.json",
            {
                "source_record_sha256": provenance.source_record_sha256,
                "source_instance_id_sha256": provenance.source_instance_id_sha256,
                "gold_validation_runs": provenance.gold_validation_runs,
                "gold_validation_passes": provenance.gold_validation_passes,
            },
        )

        candidate_safe = {
            "candidate_rank": candidate_rank,
            "gold_validation_passes": passes,
            "state": "GOLD_NOT_REPRODUCIBLE" if not provenance.task_valid else "GOLD_VALID_3_OF_3",
        }
        safe_summary["candidate_results"].append(candidate_safe)
        _json_dump(safe_root / "validator-summary.json", safe_summary)

        if not provenance.task_valid:
            continue

        task_id = stage0_control.opaque_task_id(
            instance_id=str(row["instance_id"]),
            seed_sha256=SEED_SHA256,
            ordinal=SPLIT_ORDINAL[split],
        )
        try:
            envelope = task_envelope.sanitize_for_solver(
                row,
                opaque_task_id=task_id,
                task_valid=True,
                platform="linux",
            )
        except task_envelope.TaskPublicInputError:
            candidate_safe["state"] = "GOLD_VALID_BUT_BLIND_INPUT_UNUSABLE"
            _json_dump(safe_root / "validator-summary.json", safe_summary)
            continue

        # Any other envelope/integrity failure is a harness defect and must crash.
        task_envelope.verify_solver_envelope(envelope)
        leaked = task_envelope.forbidden_key_scan(envelope)
        if leaked:
            raise ValidatorError("sanitized envelope failed forbidden-key scan")

        envelope_sha256 = hashlib.sha256(
            json.dumps(
                envelope,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        _json_dump(safe_root / "solver-envelope.json", envelope)
        candidate_safe["state"] = "ADMITTED_3_OF_3"
        safe_summary.update(
            {
                "state": "ADMITTED_3_OF_3",
                "candidate_rank": candidate_rank,
                "gold_validation_passes": 3,
                "task_id": task_id,
                "solver_envelope_sha256": envelope_sha256,
            }
        )
        _json_dump(safe_root / "validator-summary.json", safe_summary)
        print(f"SAFE_VALIDATOR_RESULT split={split} state=ADMITTED_3_OF_3 rank={candidate_rank}")
        return 0

    saw_gold_valid = any(
        row["gold_validation_passes"] == 3 for row in safe_summary["candidate_results"]
    )
    safe_summary.update(
        {
            "state": (
                "NO_USABLE_BLIND_TASK_IN_BOUNDED_PREFIX"
                if saw_gold_valid
                else "NO_REPRODUCIBLY_VALID_TASK_IN_BOUNDED_PREFIX"
            ),
            "candidate_rank": None,
            "gold_validation_passes": None,
            "task_id": None,
        }
    )
    _json_dump(safe_root / "validator-summary.json", safe_summary)
    print(
        f"SAFE_VALIDATOR_RESULT split={split} state={safe_summary['state']} "
        f"checked={min(max_candidates, len(ordered))}"
    )
    return 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", required=True, choices=sorted(SPLIT_ORDINAL))
    parser.add_argument("--evaluator-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--max-candidates", type=int, default=4)
    args = parser.parse_args()
    return run(
        split=args.split,
        evaluator_root=pathlib.Path(args.evaluator_root).resolve(),
        output_root=pathlib.Path(args.output_root).resolve(),
        max_candidates=args.max_candidates,
    )


if __name__ == "__main__":
    raise SystemExit(main())
