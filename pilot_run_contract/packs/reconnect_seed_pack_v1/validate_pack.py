from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ROOT.parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from pilot_run_contract.models import validate_seed


def validate_manifest() -> None:
    for line in (ROOT / "manifest.sha256").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        if actual != digest:
            raise SystemExit("manifest mismatch: " + name)


def main() -> None:
    validate_manifest()
    seed = json.loads((ROOT / "seed_active_scope_cut.json").read_text(encoding="utf-8"))
    validate_seed(seed)
    profiles = json.loads((ROOT / "scope_profiles.json").read_text(encoding="utf-8"))
    if profiles["active_profile"] != "P0_SCOPE_CUT" or len(profiles["profiles"]) != 7:
        raise SystemExit("scope profile mismatch")
    for name in ("README.md", "FULL_CONTEXT.md", "scope_profiles.json"):
        if not (ROOT / name).is_file():
            raise SystemExit("missing pack source: " + name)
    print("PACK READY_FOR_PILOT")


if __name__ == "__main__":
    main()
