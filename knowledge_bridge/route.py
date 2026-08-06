from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RouteDecision:
    knowledge_id: str
    destination: str
    reasons: tuple[str, ...]


def _load(root: Path, knowledge_id: str) -> dict:
    path = root / "normalized" / f"{knowledge_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"knowledge record not found: {knowledge_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def route_record(state_root: str | Path, knowledge_id: str) -> RouteDecision:
    root = Path(state_root)
    record = _load(root, knowledge_id)
    kind = record.get("knowledge_type", "idea")
    status = record.get("status", "captured")
    sensitivity = record.get("sensitivity", "internal")
    reasons: list[str] = [f"knowledge_type:{kind}", f"status:{status}"]

    if sensitivity in {"personal", "restricted"}:
        destination = "archive"
        reasons.append(f"sensitivity:{sensitivity}")
    elif kind == "test":
        destination = "test"
    elif kind == "pattern":
        destination = "pattern"
    elif kind in {"project_context", "evidence"}:
        destination = "project_context"
    elif kind in {"decision", "spec", "problem"} and status in {"challenged", "approved", "frozen"}:
        challenge_path = root / "challenges" / f"{knowledge_id}.json"
        if challenge_path.exists():
            challenge = json.loads(challenge_path.read_text(encoding="utf-8"))
            if challenge.get("promotion_ready") is True:
                destination = "freezer"
                reasons.append("challenge:promotion_ready")
            else:
                destination = "recall"
                reasons.append("challenge:not_ready")
        else:
            destination = "recall"
            reasons.append("challenge:missing")
    elif kind == "archive":
        destination = "archive"
    else:
        destination = "recall"

    result = RouteDecision(knowledge_id=knowledge_id, destination=destination, reasons=tuple(reasons))
    output = root / "routes" / f"{knowledge_id}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.exists():
        output.write_text(json.dumps({"knowledge_id": result.knowledge_id, "destination": result.destination, "reasons": list(result.reasons)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
