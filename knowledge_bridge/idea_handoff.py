from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .design_e2e import run_design_e2e


@dataclass(frozen=True)
class IdeaHandoffResult:
    handoff_path: str
    bundle_path: str
    idea_id: str
    request_id: str
    project_id: str
    decision: str
    status: str
    human_decision_recorded: bool
    implementation_executed: bool


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def handoff_approved_idea(
    routing_report: str | Path,
    repo_root: str | Path,
    output_root: str | Path,
    decision: str,
) -> IdeaHandoffResult:
    report_path = Path(routing_report).expanduser().resolve()
    output = Path(output_root).expanduser().resolve()
    normalized_decision = str(decision).strip().upper()
    if normalized_decision != "APPROVE":
        raise PermissionError("V1.1 handoff requires explicit decision=APPROVE")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite idea handoff: {output}")

    report = _load(report_path)
    if report.get("status") != "AWAITING_HUMAN_ROUTING_DECISION":
        raise ValueError("routing report is not awaiting a human routing decision")
    if report.get("routing_action") != "ROUTE_TO_V1" or report.get("timing") != "NOW":
        raise ValueError("routing report is not eligible for V1 handoff")
    if report.get("human_questions"):
        raise ValueError("routing report still has unresolved human questions")
    if report.get("missing_parts"):
        raise ValueError("routing report still has missing routing prerequisites")
    v1_payload = report.get("v1_input")
    if not isinstance(v1_payload, dict):
        raise ValueError("routing report does not contain a V1 input payload")

    output.mkdir(parents=True)
    approved_input = output / "approved-v1-input.json"
    approved_input.write_text(json.dumps(v1_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    bundle = output / "bundle"
    result = run_design_e2e(approved_input, repo_root, bundle)

    decision_record = {
        "schema_version": "1.1",
        "idea_id": report["idea_id"],
        "routing_report": str(report_path),
        "decision": "APPROVE",
        "routing_action": "ROUTE_TO_V1",
        "request_id": result.request_id,
        "project_id": result.project_id,
        "bundle": "bundle",
        "status": "HANDED_OFF_TO_V1_AWAITING_HUMAN_DECISION",
        "human_decision_recorded": True,
        "implementation_executed": False,
    }
    handoff = output / "handoff.json"
    handoff.write_text(json.dumps(decision_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(report_path, output / "routing-report.json")

    return IdeaHandoffResult(
        handoff_path=str(handoff),
        bundle_path=str(bundle),
        idea_id=str(report["idea_id"]),
        request_id=result.request_id,
        project_id=result.project_id,
        decision="APPROVE",
        status="HANDED_OFF_TO_V1_AWAITING_HUMAN_DECISION",
        human_decision_recorded=True,
        implementation_executed=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Record explicit human approval and hand a V1.1 routing proposal to the existing V1.0 design pipeline")
    parser.add_argument("--routing", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--decision", required=True, choices=["APPROVE"])
    args = parser.parse_args()
    result = handoff_approved_idea(args.routing, args.repo, args.output, args.decision)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
