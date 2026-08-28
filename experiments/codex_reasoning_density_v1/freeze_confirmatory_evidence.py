#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_SUFFIXES = (".jsonl", ".json", ".txt", ".log")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--dest-root", default="experiments/codex_reasoning_density_v1/evidence", type=Path)
    ns = ap.parse_args()
    src = ns.source.resolve()
    summary = src / "confirmatory_summary.json"
    if not summary.is_file():
        raise SystemExit("ERROR: confirmatory_summary.json missing")
    report = json.loads(summary.read_text(encoding="utf-8"))
    if report.get("result") != "CONFIRMED_STRICT_WIN":
        raise SystemExit("ERROR: refusing to freeze non-confirmed result")

    dest = ns.dest_root / src.name
    if dest.exists():
        raise SystemExit(f"ERROR: destination already exists: {dest}")
    dest.mkdir(parents=True)

    copied = []
    for p in sorted(src.iterdir()):
        if not p.is_file() or p.suffix not in ALLOWED_SUFFIXES:
            continue
        if p.name.endswith(".stderr.log") and p.stat().st_size == 0:
            continue
        target = dest / p.name
        shutil.copy2(p, target)
        copied.append(target)

    files = []
    for p in copied:
        files.append({"path": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)})

    manifest = {
        "schema": "codex-confirmatory-evidence-bundle/v1",
        "source_directory_name": src.name,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "result": report.get("result"),
        "pair_count": report.get("pair_count"),
        "strict_pair_wins": report.get("strict_pair_wins"),
        "median_total_input_reduction": report.get("median_total_input_reduction"),
        "median_uncached_input_reduction": report.get("median_uncached_input_reduction"),
        "median_wall_time_reduction": report.get("median_wall_time_reduction"),
        "quality_relations": report.get("quality_relations"),
        "files": files,
        "invariant": "Manifest hashes freeze observed benchmark artifacts; historical evidence does not grant current authority.",
    }
    (dest / "evidence_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"destination": str(dest), "manifest": manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
