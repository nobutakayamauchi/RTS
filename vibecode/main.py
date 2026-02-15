from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


# Paths
EXECUTION_LOG = Path("logs/EXECUTION_LOG.md")
PROPOSALS = Path("evolution/PROPOSALS.md")
ACTIVE_PROPOSALS = Path("evolution/ACTIVE_PROPOSALS.md")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def ensure_file(path: Path, header: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(header + "\n", encoding="utf-8")


def append_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(text)


def log_execution(event: str, status: str = "ACTIVE", integrity: str = "VERIFIED") -> None:
    ts = utc_now_iso()
    block = (
        f"\n---\n"
        f"## {ts}\n"
        f"Event: {event}\n"
        f"Status: {status}\n"
        f"Integrity: {integrity}\n"
        f"---\n"
    )
    append_md(EXECUTION_LOG, block)


def add_proposal_to_active(
    proposal_id: str,
    proposed_by: str,
    change_description: str,
    reason: str,
    status: str = "PENDING",
    approved_by: str = "",
    approval_reason: str = "",
) -> None:
    ts = utc_now_iso()
    block = (
        f"\n---\n"
        f"## Proposal ID: {proposal_id}\n"
        f"Timestamp: {ts}\n"
        f"Proposed by: {proposed_by}\n"
        f"Change description: {change_description}\n"
        f"Reason: {reason}\n"
        f"Status: {status}\n"
        f"Approved by: {approved_by}\n"
        f"Approval reason: {approval_reason}\n"
        f"---\n"
    )

    # ACTIVE_PROPOSALS に追記（現時点はテンプレ運用でOK）
    append_md(ACTIVE_PROPOSALS, block)


def main() -> None:
    # Ensure base files exist
    ensure_file(EXECUTION_LOG, "# RTS Execution Log\n")
    ensure_file(PROPOSALS, "# RTS Evolution Proposals\n")
    ensure_file(
        ACTIVE_PROPOSALS,
        "# RTS Active Evolution Proposals\n\n"
        "Status definitions:\n\n"
        "PENDING  = awaiting originator decision\n"
        "APPROVED = authorized and ready to integrate\n"
        "REJECTED = denied\n\n"
        "Only the originator may approve proposals.\n",
    )

    # Execution cycle
    log_execution("RTS execution cycle started")

    # ここは“自動で提案を1本起票する”サンプル（要らなければ後でOFFにしてOK）
    proposal_id = "RTS-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    add_proposal_to_active(
        proposal_id=proposal_id,
        proposed_by="RTS CORE",
        change_description="Log execution cycle events to RTS markdown logs",
        reason="Ensure auditability and reproducible operational history",
        status="PENDING",
    )

    log_execution("RTS execution cycle completed")


if __name__ == "__main__":
    main()
