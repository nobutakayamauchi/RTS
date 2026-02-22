from __future__ import annotations

import json
import datetime as _dt
import hashlib
from pathlib import Path
from typing import Dict, List


INDEX_VERSION = "0.1"


def _utc_now_iso() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _collect_files(root: Path, rel_dir: str, patterns: List[str]) -> List[Dict]:
    base = root / rel_dir
    items: List[Dict] = []
    if not base.exists():
        return items

    for pat in patterns:
        for p in sorted(base.glob(pat)):
            if p.is_file():
                items.append({
                    "path": str(p.relative_to(root)).replace("\\", "/"),
                    "bytes": p.stat().st_size,
                    "mtime_utc": _dt.datetime.utcfromtimestamp(p.stat().st_mtime).replace(microsecond=0).isoformat() + "Z",
                    "sha256": _sha256_file(p),
                })
    return items


def build_index(repo_root: str | Path = ".", out_path: str | Path = "rts_index.json") -> Dict:
    root = Path(repo_root)

    index = {
        "schema": "rts.memory_index",
        "version": INDEX_VERSION,
        "generated_utc": _utc_now_iso(),
        "collections": {
            "logs": _collect_files(root, "logs", ["*.md", "*.txt", "*.json"]),
            "incidents": _collect_files(root, "incidents", ["**/*.md", "**/*.json", "**/*.txt"]),
            "radar": _collect_files(root, "radar", ["**/*.md", "**/*.json", "**/*.txt"]),
            "governance": _collect_files(root, ".", ["CORE_MANIFEST.md", "RTS_CHARTER.md", "RTS_DECLARATION.md", "RTS_RECOGNITION.md", "RTS_VERSION_1_0_MILESTONE.md"]),
        },
        "notes": [
            "Index is evidence-friendly: includes sha256 and mtime for change detection.",
            "This file is safe to regenerate; integrity checks compare append-only logs separately.",
        ],
    }

    outp = root / out_path
    outp.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index
