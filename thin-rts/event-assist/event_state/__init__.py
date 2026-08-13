from __future__ import annotations

import sys
from pathlib import Path

if __package__:
    from .base import EventStateError, IMPLEMENTATION_ID, REPORT_SCHEMA, SCHEMA, canonical_json_bytes
    from .runtime import cli, load_case, validate_case
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from event_state.base import EventStateError, IMPLEMENTATION_ID, REPORT_SCHEMA, SCHEMA, canonical_json_bytes
    from event_state.runtime import cli, load_case, validate_case

__all__ = [
    "EventStateError",
    "IMPLEMENTATION_ID",
    "REPORT_SCHEMA",
    "SCHEMA",
    "canonical_json_bytes",
    "cli",
    "load_case",
    "validate_case",
]

if __name__ == "__main__":
    raise SystemExit(cli())
