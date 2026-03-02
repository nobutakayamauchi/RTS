#!/usr/bin/env python3
import os, json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    month = os.environ.get("RTS_MONTH")
    if not month:
        print("RTS_MONTH not set")
        return 1

    decision_id = os.environ.get("DECISION_ID", "manual-decision")
    actor = os.environ.get("ACTOR", "unknown")
    role = os.environ.get("ACTOR_ROLE", "operator")
    scope = os.environ.get("SCOPE", "unspecified")
    justification = os.environ.get("JUSTIFICATION", "")
    head_sha = os.environ.get("HEAD_SHA", "")

    ts = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    payload = {
        "ts": ts,
        "kind": "decision.boundary",
        "decision_id": decision_id,
        "actor": actor,
        "actor_role": role,
        "state_hash": head_sha,
        "scope": scope,
        "justification": justification
    }

    base = ROOT / "sessions" / month
    base.mkdir(parents=True, exist_ok=True)

    target = base / "session_boundary.jsonl"

    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    print("decision boundary appended")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
