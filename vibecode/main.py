from datetime import datetime
from pathlib import Path

EXECUTION_LOG = Path("logs/EXECUTION_LOG.md")
ACTIVE_PROPOSALS = Path("evolution/ACTIVE_PROPOSALS.md")

def now_iso_z() -> str:
    # e.g. 2026-02-15T21:49:38.930883Z
    return datetime.utcnow().isoformat(timespec="microseconds") + "Z"

def append_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(text)

def log_execution(event: str, source: str = "GitHub Actions", operator: str = "RTS Core") -> None:
    block = (
        f"\n## {now_iso_z()}\n"
        f"Event: {event}\n"
        f"Source: {source}\n"
        f"Operator: {operator}\n\n"
        f"Status: ACTIVE\n"
        f"Integrity: VERIFIED\n"
        f"---\n"
    )
    append_text(EXECUTION_LOG, block)

def has_pending_proposals() -> bool:
    if not ACTIVE_PROPOSALS.exists():
        return False
    text = ACTIVE_PROPOSALS.read_text(encoding="utf-8", errors="ignore")
    # 「PENDING」が1つでもあれば、提案は増やさない
    return "Status: PENDING" in text

def ensure_active_template() -> None:
    if ACTIVE_PROPOSALS.exists():
        return
    template = (
        "# RTS Active Evolution Proposals\n\n"
        "This file contains proposals that have not yet been approved.\n\n"
        "Status definitions:\n\n"
        "PENDING  = awaiting originator decision\n"
        "APPROVED = authorized and ready to integrate\n"
        "REJECTED = denied\n\n"
        "Only the originator may approve proposals.\n\n"
        "---\n\n"
        "No active proposals.\n"
    )
    append_text(ACTIVE_PROPOSALS, template)

def propose_evolution(change_description: str, reason: str, proposed_by: str = "RTS CORE") -> None:
    proposal_id = "RTS-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    proposal = (
        "\n---\n\n"
        f"## Proposal ID: {proposal_id}\n\n"
        f"Timestamp: {now_iso_z()}\n"
        f"Proposed by: {proposed_by}\n"
        f"Change description: {change_description}\n"
        f"Reason: {reason}\n\n"
        "Status: PENDING\n"
        "Approved by:\n"
        "Approval reason:\n"
    )

    # まだ "No active proposals." が残ってたら、消してから追記
    if ACTIVE_PROPOSALS.exists():
        text = ACTIVE_PROPOSALS.read_text(encoding="utf-8", errors="ignore")
        if "No active proposals." in text:
            text = text.replace("No active proposals.\n", "")
            ACTIVE_PROPOSALS.write_text(text, encoding="utf-8")

    append_text(ACTIVE_PROPOSALS, proposal)

def main():
    ensure_active_template()

    log_execution("RTS execution cycle started")

    if has_pending_proposals():
        # 重要：PENDING がある間は増殖しない
        log_execution("RTS decision: skipped proposal (pending exists)")
    else:
        propose_evolution(
            change_description="Introduce RTS decision core to prevent proposal spam and enforce governance.",
            reason="Maintain auditable evolution while avoiding uncontrolled self-evolution loops.",
        )
        log_execution("RTS decision: created proposal")

    log_execution("RTS execution cycle completed")

if __name__ == "__main__":
    main()
