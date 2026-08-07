from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CityReleaseResult:
    report_path: str
    markdown_path: str
    request_id: str
    project_id: str
    release: str
    decision: str
    next_city: str
    human_decision_required: bool


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def audit_city_release(bundle_path: str | Path, lifecycle_path: str | Path, output_path: str | Path) -> CityReleaseResult:
    bundle = Path(bundle_path).expanduser().resolve()
    lifecycle_file = Path(lifecycle_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    markdown = output.with_suffix(".md")
    if output.exists() or markdown.exists():
        raise FileExistsError(f"refusing to overwrite city release report: {output}")

    translation = _load(bundle / "translation.json")
    summary = _load(bundle / "summary.json")
    lifecycle = _load(lifecycle_file)
    request_id = translation["request_id"]
    project_id = translation["project_id"]
    if summary.get("request_id") != request_id or lifecycle.get("request_id") != request_id:
        raise ValueError("request identity does not match across release evidence")
    if summary.get("project_id") != project_id or lifecycle.get("project_id") != project_id:
        raise ValueError("project identity does not match across release evidence")
    if summary.get("implementation_executed") is not False:
        raise PermissionError("release audit requires a non-executing design bundle")
    if lifecycle.get("approval", {}).get("implementation_executed") is not False:
        raise PermissionError("release audit refuses lifecycle evidence reporting execution")

    counts = lifecycle.get("counts", {})
    broken = int(counts.get("broken", 0))
    stale = int(counts.get("stale", 0))
    orphan = int(counts.get("orphan", 0))
    unobserved = int(counts.get("unobserved", 0))

    blockers = []
    if broken:
        blockers.append(f"{broken} planned item(s) are BROKEN")
    if stale:
        blockers.append(f"{stale} planned item(s) are STALE")
    if orphan:
        blockers.append(f"{orphan} observation(s) are not linked to the plan")
    constraints = [
        "Human approval remains mandatory before implementation.",
        "Screenshot and sketch understanding remain adapter inputs, not autonomous design authority.",
        "The common UI is a review surface, not an editor or repair console.",
        "Debug observations are evidence and never trigger automatic repair.",
    ]
    freeze_scope = [
        "Design & Function Translator contract v1",
        "Translator-to-Council design E2E",
        "Thin Obsidian intake and review adapter",
        "Five-section common review UI",
        "Planned / As Built / Broken / Stale lifecycle linking",
        "Human-decision safety gate",
    ]
    v2_backlog = [
        "Real project dogfooding and observation capture",
        "Screenshot and hand-drawn sketch analysis adapter",
        "Interactive graph navigation and lifecycle filters",
        "Approval recording with an auditable decision ledger",
        "PDF and slide exports for external stakeholders",
    ]
    next_city = "DOGFOODING"
    decision = "V1_SCOPE_COMPLETE_WITH_KNOWN_ISSUES" if blockers else "V1_SCOPE_COMPLETE"
    report = {
        "schema_version": "1.0",
        "release": "Design Function Translation Vertical Slice V1",
        "request_id": request_id,
        "project_id": project_id,
        "decision": decision,
        "freeze_scope": freeze_scope,
        "known_constraints": constraints,
        "release_blockers_for_production": blockers,
        "unobserved_count": unobserved,
        "next_city": next_city,
        "why_next": "Exercise the completed vertical slice on an existing real project before expanding Obsidian, UI, or debug infrastructure.",
        "v2_backlog": v2_backlog,
        "do_not_build_now": [
            "Full Obsidian rewrite",
            "Production-grade visual editor",
            "Automatic repair or approval",
            "Multi-city feature expansion before dogfooding evidence",
        ],
        "human_decision_required": True,
        "implementation_executed": False,
        "status": "AWAITING_HUMAN_RELEASE_DECISION",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown.write_text(_markdown(report), encoding="utf-8")
    return CityReleaseResult(
        report_path=str(output),
        markdown_path=str(markdown),
        request_id=request_id,
        project_id=project_id,
        release=report["release"],
        decision=decision,
        next_city=next_city,
        human_decision_required=True,
    )


def _items(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values) or "- None"


def _markdown(report: dict[str, Any]) -> str:
    return f"""# RTS V1 City Release Audit

## Decision

- Release: `{report['release']}`
- Decision: `{report['decision']}`
- Status: `{report['status']}`
- Next city: `{report['next_city']}`

## V1 freeze scope

{_items(report['freeze_scope'])}

## Known constraints

{_items(report['known_constraints'])}

## Production blockers

{_items(report['release_blockers_for_production'])}

## Why this city is next

{report['why_next']}

## V2 backlog

{_items(report['v2_backlog'])}

## Do not build now

{_items(report['do_not_build_now'])}

This report records a proposed release boundary only. No approval, repair, code modification, or implementation was executed.
"""
