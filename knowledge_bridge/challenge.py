from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .connect import connect_record


@dataclass(frozen=True)
class ChallengeFinding:
    code: str
    severity: str
    question: str
    resolved: bool


@dataclass(frozen=True)
class ChallengeResult:
    knowledge_id: str
    promotion_ready: bool
    findings: tuple[ChallengeFinding, ...]
    connection_count: int


def challenge_record(state_root: str | Path, knowledge_id: str) -> ChallengeResult:
    root = Path(state_root)
    path = root / "normalized" / f"{knowledge_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"knowledge record not found: {knowledge_id}")
    record = json.loads(path.read_text(encoding="utf-8"))
    body = str(record.get("body", "")).strip()
    metadata = record.get("frontmatter", {})
    findings: list[ChallengeFinding] = []

    checks = (
        ("PURPOSE_MISSING", "high", "What exact problem and intended outcome does this record address?", not bool(metadata.get("purpose") or metadata.get("intent") or len(body) >= 40)),
        ("CONSTRAINTS_MISSING", "medium", "Which technical, financial, time, device, health, or operational constraints apply?", not bool(metadata.get("constraints"))),
        ("ACCEPTANCE_MISSING", "high", "What observable conditions prove this is complete?", not bool(metadata.get("acceptance_criteria") or metadata.get("done_when"))),
        ("TEST_MISSING", "high", "How will the claim or implementation be tested?", not bool(metadata.get("test_plan") or metadata.get("tests"))),
        ("ALTERNATIVES_MISSING", "medium", "Which alternatives were rejected, and why?", not bool(metadata.get("rejected_alternatives") or metadata.get("alternatives"))),
        ("ROLLBACK_MISSING", "medium", "What is the rollback or safe-stop boundary?", not bool(metadata.get("rollback"))),
        ("AUTHORITY_UNCLEAR", "high", "Is this an observation, proposal, approved decision, or frozen specification?", str(record.get("status", "captured")) not in {"approved", "frozen", "challenged"}),
        ("SOURCE_WEAK", "medium", "Is the source evidence sufficient and traceable?", not bool(record.get("source_hash") and record.get("source_path"))),
        ("SENSITIVITY_BLOCK", "high", "Does this record require private handling or redaction?", record.get("sensitivity") in {"personal", "restricted"}),
        ("CONFIDENCE_LOW", "medium", "What evidence would raise classification confidence?", float(record.get("confidence", 0)) < 0.7),
    )
    for code, severity, question, unresolved in checks:
        findings.append(ChallengeFinding(code, severity, question, not unresolved))

    connections = connect_record(root, knowledge_id)
    for connection in connections:
        if connection.relation == "possible_contradiction":
            findings.append(ChallengeFinding("POSSIBLE_CONTRADICTION", "high", f"Resolve the possible contradiction with {connection.other_knowledge_id}; do not overwrite either record.", False))
        elif connection.relation == "duplicate":
            findings.append(ChallengeFinding("POSSIBLE_DUPLICATE", "medium", f"Decide whether {connection.other_knowledge_id} is a duplicate, superseded record, or intentional restatement.", False))

    blocking = [item for item in findings if not item.resolved and item.severity == "high"]
    result = ChallengeResult(knowledge_id, not blocking, tuple(findings), len(connections))
    output = root / "challenges" / f"{knowledge_id}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    # Challenge files are derived state, not immutable evidence. Always refresh
    # them so routing never consumes a stale pre-fix or pre-edit verdict.
    output.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
