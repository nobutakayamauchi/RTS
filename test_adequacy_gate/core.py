from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


class TestAdequacyError(ValueError):
    pass


REPORT_SCHEMA_VERSION = "false-green-test-adequacy-report/v1"
AUTHORITY_NONE = "NONE"
TARGET_TESTS = (
    "tests.test_human_escalation_gate",
    "tests.test_human_escalation_gate_da",
)


# Mutation operators are deliberately narrow and source-shape-bound. If K1
# changes so an operator no longer matches exactly once, that mutant is STALE,
# not silently skipped and not counted as a kill.
MUTATIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "M01_ROUTE_REMAINS_BUT_HUMAN_CANDIDATE",
        "kind": "CRITICAL",
        "old": '        elif active_routes:\n            disposition = "AI_CONTINUE"\n',
        "new": '        elif active_routes:\n            disposition = "HUMAN_CANDIDATE"\n',
    },
    {
        "id": "M02_SAFE_DEFER_IGNORED",
        "kind": "CRITICAL",
        "old": '        elif safe_defer is not None:\n            disposition = "WAIT_SAFE_DEFER"\n',
        "new": '        elif safe_defer is not None:\n            disposition = "HUMAN_CANDIDATE"\n',
    },
    {
        "id": "M03_HUMAN_CHOICE_BYPASSES_EXHAUSTION",
        "kind": "CRITICAL",
        "old": '        elif exhaustion_search_observed and human_choice:\n',
        "new": '        elif human_choice:\n',
    },
    {
        "id": "M04_EARLY_SEARCH_COUNTS_AS_EXHAUSTION",
        "kind": "CRITICAL",
        "old": '                elif not active_routes and row["outcome"] in {"OBSERVED", "REFUTED", "NON_DISCRIMINATING"}:\n',
        "new": '                elif row["outcome"] in {"OBSERVED", "REFUTED", "NON_DISCRIMINATING"}:\n',
    },
    {
        "id": "M05_DUPLICATE_PROBE_ALLOWED",
        "kind": "CRITICAL",
        "old": '        if row["probe_fingerprint"] in seen_probe_fingerprints:\n            raise HumanEscalationError("equivalent/replayed probe fingerprint is forbidden")\n',
        "new": '        if False and row["probe_fingerprint"] in seen_probe_fingerprints:\n            raise HumanEscalationError("equivalent/replayed probe fingerprint is forbidden")\n',
    },
    {
        "id": "M06_LOW_PRIORITY_HEURISTIC_PROMOTION",
        "kind": "CRITICAL",
        "old": '        active_recovered_routes = recovered_routes if k0.get("classification") == "HUMAN_NOW" else []\n',
        "new": '        active_recovered_routes = recovered_routes\n',
    },
    {
        "id": "M07_UNKNOWN_ROUTE_CLOSURE_ALLOWED",
        "kind": "CRITICAL",
        "old": '            if unknown_closures:\n                raise HumanEscalationError(\n',
        "new": '            if False and unknown_closures:\n                raise HumanEscalationError(\n',
    },
    {
        "id": "C01_EQUIVALENT_COMMENT",
        "kind": "EQUIVALENT_CONTROL",
        "old": '        # K1 is an escalation gate, not a work scheduler. Second-pass heuristic\n',
        "new": '        # K1 remains an escalation gate, not a work scheduler. Second-pass heuristic\n',
    },
    {
        "id": "C02_INVALID_SYNTAX",
        "kind": "INVALID_CONTROL",
        "old": 'ALLOWED_EVIDENCE_OUTCOMES = {\n',
        "new": 'ALLOWED_EVIDENCE_OUTCOMES = { ???\n',
    },
)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _tail(text: str, limit: int = 5000) -> str:
    return text[-limit:] if len(text) > limit else text


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def _test_command() -> list[str]:
    return [sys.executable, "-m", "unittest", *TARGET_TESTS, "-v"]


def _prepare_temp_package(repo_root: Path, source_text: str) -> tuple[tempfile.TemporaryDirectory[str], Path, dict[str, str]]:
    temp = tempfile.TemporaryDirectory(prefix="rts-k2-mutant-")
    root = Path(temp.name)
    shutil.copytree(repo_root / "human_escalation_gate", root / "human_escalation_gate")
    (root / "human_escalation_gate" / "core.py").write_text(source_text)
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # cwd=temp root makes the mutant package win; repo remains available for
    # tests and upstream dependencies via PYTHONPATH.
    env["PYTHONPATH"] = os.pathsep.join([str(root), str(repo_root)])
    return temp, root, env


def _execute_source(repo_root: Path, source_text: str) -> dict[str, Any]:
    temp, root, env = _prepare_temp_package(repo_root, source_text)
    try:
        smoke = _run(
            [sys.executable, "-c", "import human_escalation_gate; print(human_escalation_gate.__file__)"],
            cwd=root,
            env=env,
            timeout=30,
        )
        if smoke.returncode != 0:
            return {
                "load_ok": False,
                "tests_ran": False,
                "test_returncode": None,
                "output_tail": _tail(smoke.stdout),
            }
        tests = _run(_test_command(), cwd=root, env=env)
        return {
            "load_ok": True,
            "tests_ran": True,
            "test_returncode": tests.returncode,
            "output_tail": _tail(tests.stdout),
        }
    finally:
        temp.cleanup()


def run_mutation_suite(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root or Path(__file__).resolve().parents[1]).resolve()
    source_path = root / "human_escalation_gate" / "core.py"
    original_bytes = source_path.read_bytes()
    original = original_bytes.decode("utf-8")
    original_hash = _sha256(original_bytes)

    baseline = _execute_source(root, original)
    if not baseline["load_ok"] or baseline["test_returncode"] != 0:
        raise TestAdequacyError("baseline K1 targeted tests must pass before mutation testing")

    results: list[dict[str, Any]] = []
    for mutation in MUTATIONS:
        old = mutation["old"]
        count = original.count(old)
        if count != 1:
            results.append({
                "id": mutation["id"],
                "kind": mutation["kind"],
                "status": "STALE_OPERATOR",
                "match_count": count,
                "load_ok": None,
                "tests_ran": False,
                "output_tail": "",
            })
            continue
        mutated = original.replace(old, mutation["new"], 1)
        execution = _execute_source(root, mutated)
        if not execution["load_ok"]:
            status = "INVALID_MUTANT"
        elif execution["test_returncode"] == 0:
            status = "SURVIVED"
        else:
            status = "KILLED"
        results.append({
            "id": mutation["id"],
            "kind": mutation["kind"],
            "status": status,
            "match_count": count,
            **execution,
        })

    post_hash = _sha256(source_path.read_bytes())
    if post_hash != original_hash:
        raise TestAdequacyError("mutation suite changed production K1 source")

    critical = [r for r in results if r["kind"] == "CRITICAL"]
    equivalent = [r for r in results if r["kind"] == "EQUIVALENT_CONTROL"]
    invalid = [r for r in results if r["kind"] == "INVALID_CONTROL"]
    mutation_lane_pass = bool(critical) and all(r["status"] == "KILLED" for r in critical)
    controls_pass = (
        bool(equivalent)
        and all(r["status"] == "SURVIVED" for r in equivalent)
        and bool(invalid)
        and all(r["status"] == "INVALID_MUTANT" for r in invalid)
    )
    return {
        "schema_version": "false-green-mutation-report/v1",
        "source_sha256_before": original_hash,
        "source_sha256_after": post_hash,
        "target_tests": list(TARGET_TESTS),
        "baseline": baseline,
        "results": results,
        "audit": {
            "critical_total": len(critical),
            "critical_killed": sum(r["status"] == "KILLED" for r in critical),
            "invalid_not_counted_as_kill": True,
            "mutation_lane_pass": mutation_lane_pass,
            "controls_pass": controls_pass,
            "production_source_unchanged": post_hash == original_hash,
        },
    }


def evaluate_test_adequacy(
    mutation_report: dict[str, Any],
    *,
    known_bad: list[dict[str, Any]],
    held_out: list[dict[str, Any]],
    metamorphic: list[dict[str, Any]],
) -> dict[str, Any]:
    for name, rows in (("known_bad", known_bad), ("held_out", held_out), ("metamorphic", metamorphic)):
        if not rows:
            raise TestAdequacyError(f"{name} lane must not be empty")
        ids = [row.get("case_id") for row in rows]
        if any(not isinstance(case_id, str) or not case_id for case_id in ids) or len(ids) != len(set(ids)):
            raise TestAdequacyError(f"{name} lane requires unique non-empty case_id values")
        if any(set(row) != {"case_id", "passed", "detail"} for row in rows):
            raise TestAdequacyError(f"{name} lane rows require case_id, passed, detail only")
        if any(not isinstance(row["passed"], bool) for row in rows):
            raise TestAdequacyError(f"{name} lane passed must be boolean")

    mutation_pass = bool(mutation_report.get("audit", {}).get("mutation_lane_pass"))
    controls_pass = bool(mutation_report.get("audit", {}).get("controls_pass"))
    source_unchanged = bool(mutation_report.get("audit", {}).get("production_source_unchanged"))
    lane_status = {
        "mutation": mutation_pass,
        "harness_controls": controls_pass,
        "known_bad": all(row["passed"] for row in known_bad),
        "held_out": all(row["passed"] for row in held_out),
        "metamorphic": all(row["passed"] for row in metamorphic),
        "production_source_unchanged": source_unchanged,
    }
    adequate = all(lane_status.values())
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": "ADEQUATE" if adequate else "HOLD_FALSE_GREEN_RISK",
        "lanes": lane_status,
        "known_bad": known_bad,
        "held_out": held_out,
        "metamorphic": metamorphic,
        "mutation_report": mutation_report,
        "audit": {
            "all_mandatory_lanes_required": True,
            "single_percentage_is_sufficient": False,
            "test_pass_proves_bug_absence": False,
            "invalid_mutant_counts_as_kill": False,
        },
        "execution_authority": AUTHORITY_NONE,
        "profile_application_authority": AUTHORITY_NONE,
        "promotion_authority": AUTHORITY_NONE,
        "canon_authority": AUTHORITY_NONE,
        "semantic_truth_authority": AUTHORITY_NONE,
    }


def verify_test_adequacy_report(report: dict[str, Any]) -> None:
    if report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise TestAdequacyError("unexpected adequacy report schema")
    lanes = report.get("lanes")
    if not isinstance(lanes, dict) or not lanes:
        raise TestAdequacyError("adequacy lanes are required")
    expected = "ADEQUATE" if all(lanes.values()) else "HOLD_FALSE_GREEN_RISK"
    if report.get("status") != expected:
        raise TestAdequacyError("adequacy status does not match lane results")
    for field in (
        "execution_authority",
        "profile_application_authority",
        "promotion_authority",
        "canon_authority",
        "semantic_truth_authority",
    ):
        if report.get(field) != AUTHORITY_NONE:
            raise TestAdequacyError(f"{field} must remain NONE")
    if report.get("audit", {}).get("invalid_mutant_counts_as_kill") is not False:
        raise TestAdequacyError("invalid mutants must not count as kills")
    if report.get("audit", {}).get("test_pass_proves_bug_absence") is not False:
        raise TestAdequacyError("test pass must not claim bug absence")


def report_fingerprint(report: dict[str, Any]) -> str:
    payload = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()
