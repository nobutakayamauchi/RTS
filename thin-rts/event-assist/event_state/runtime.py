from __future__ import annotations

from .base import (
    Any,
    argparse,
    copy,
    json,
    Path,
    sys,
    EVENT_TRUTH_STATES,
    GAP_STATES,
    IMPLEMENTATION_ID,
    REPORT_SCHEMA,
    SCHEMA,
    EventStateError,
    _parse_time,
    _require_dict,
    _require_list,
    _require_str,
    _validate_evidence,
    _validate_facts,
    _validate_sources,
    canonical_json_bytes,
)
from .rules import (
    _validate_actions,
    _validate_authorities,
    _validate_decisions,
    _validate_documents,
    _watch_report,
)
def validate_case(case: dict[str, Any], *, evaluated_at: str) -> dict[str, Any]:
    obj = copy.deepcopy(_require_dict(case, "case"))
    if obj.get("schema") != SCHEMA:
        raise EventStateError(f"unsupported schema: {obj.get('schema')!r}")
    _require_str(obj.get("event_id"), "event_id")
    _require_str(obj.get("event_type"), "event_type")
    truth = _require_str(obj.get("event_truth_state"), "event_truth_state")
    if truth not in EVENT_TRUTH_STATES:
        raise EventStateError(f"unsupported event_truth_state: {truth}")
    _parse_time(obj.get("observed_at"), "observed_at")
    if obj.get("event_time") is not None:
        _parse_time(obj["event_time"], "event_time")
    _require_str(obj.get("event_source_ref"), "event_source_ref")
    unknowns = _require_list(obj.get("unknowns", []), "unknowns")
    if not all(isinstance(v, str) and v for v in unknowns):
        raise EventStateError("unknowns must contain non-empty strings")

    evaluated = _parse_time(evaluated_at, "evaluated_at")
    sources = _validate_sources(obj)
    facts = _validate_facts(obj, sources)
    authorities = _validate_authorities(obj)
    evidence = _validate_evidence(obj, sources)
    _validate_decisions(obj)
    actions = _validate_actions(obj, sources, facts, authorities, evaluated)
    documents = _validate_documents(obj, sources, facts, evidence, authorities, evaluated)
    watches = _watch_report(obj, evaluated, sources)

    evidence_gaps: list[dict[str, Any]] = []
    for ev in evidence.values():
        if ev["status"] in GAP_STATES:
            evidence_gaps.append(
                {
                    "evidence_id": ev["evidence_id"],
                    "evidence_class": ev["evidence_class"],
                    "status": ev["status"],
                    "collection_authority": ev["collection_authority"],
                }
            )

    action_pins: list[dict[str, Any]] = []
    for action in actions.values():
        pin = {
            "action_id": action["action_id"],
            "pin_class": action["pin_class"],
            "assertion_state": action["assertion_state"],
            "next_action": action["next_action"],
            "source_refs": action.get("source_refs", []),
        }
        if action.get("deadline") is not None:
            pin["deadline"] = action["deadline"]
            deadline_at = _parse_time(action["deadline"], f"action {action['action_id']}.deadline")
            pin["deadline_state"] = "OVERDUE" if evaluated > deadline_at else "UPCOMING"
        if action.get("authority_required") is not None:
            pin["authority_required"] = action["authority_required"]
            pin["authority_state"] = authorities[action["authority_required"]]
        action_pins.append(pin)

    for ev in evidence_gaps:
        synthetic_id = f"gap:{ev['evidence_id']}"
        if synthetic_id not in {p["action_id"] for p in action_pins}:
            action_pins.append(
                {
                    "action_id": synthetic_id,
                    "pin_class": "EVIDENCE_GAP",
                    "assertion_state": "VERIFIED",
                    "next_action": "Review the evidence gap and use an authorized existing acquisition path if available.",
                    "source_refs": [],
                    "authority_required": "collect",
                    "authority_state": authorities["collect"],
                }
            )

    for watch in watches:
        if watch["status"] == "WATCH_DEGRADED":
            action_pins.append(
                {
                    "action_id": f"watch:{watch['watch_id']}",
                    "pin_class": "WATCH_DEGRADED",
                    "assertion_state": "VERIFIED",
                    "next_action": "Restore or replace the external watch before treating prior results as current coverage.",
                    "source_refs": [],
                }
            )

    document_report: list[dict[str, Any]] = []
    for doc in documents.values():
        document_report.append(
            {
                "document_id": doc["document_id"],
                "state": doc["state"],
                "submission_authority": authorities["submit"],
            }
        )

    blocked = []
    if truth in {"DISPUTED", "UNKNOWN"}:
        blocked.append("EVENT_TRUTH_NOT_CONFIRMED")
    if unknowns:
        blocked.append("MATERIAL_UNKNOWNS_PRESENT")
    if any(ev["status"] in GAP_STATES for ev in evidence.values()):
        blocked.append("EVIDENCE_GAPS_PRESENT")
    if any(w["status"] == "WATCH_DEGRADED" for w in watches):
        blocked.append("WATCH_DEGRADED")
    if any(
        action.get("authority_required") is not None
        and authorities[action["authority_required"]] != "AUTHORIZED"
        for action in actions.values()
    ):
        blocked.append("ACTION_AUTHORITY_BLOCKED")
    if any(pin.get("deadline_state") == "OVERDUE" for pin in action_pins):
        blocked.append("DEADLINE_OVERDUE")

    report = {
        "schema": REPORT_SCHEMA,
        "implementation_id": IMPLEMENTATION_ID,
        "event_id": obj["event_id"],
        "evaluated_at": evaluated_at,
        "event_truth_state": truth,
        "evidence_gaps": sorted(evidence_gaps, key=lambda v: v["evidence_id"]),
        "action_pins": sorted(action_pins, key=lambda v: v["action_id"]),
        "watches": watches,
        "documents": sorted(document_report, key=lambda v: v["document_id"]),
        "authority": authorities,
        "unknowns": list(unknowns),
        "blocking_states": sorted(set(blocked)),
        "classification": "PASS" if not blocked else "UNKNOWN_OR_BLOCKED",
    }
    return report


def load_case(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise EventStateError(f"case file missing/unsafe: {path}")
    try:
        value = json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EventStateError(f"case file is invalid JSON: {path}") from exc
    return _require_dict(value, "case")


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    goal = sub.add_parser("goal", help="validate one event case and emit the mechanical state report")
    goal.add_argument("case", type=Path)
    goal.add_argument("--at", required=True, help="evaluation time in ISO-8601 with timezone")
    goal.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        report = validate_case(load_case(args.case), evaluated_at=args.at)
    except EventStateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    payload = canonical_json_bytes(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(payload)
    else:
        sys.stdout.buffer.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
