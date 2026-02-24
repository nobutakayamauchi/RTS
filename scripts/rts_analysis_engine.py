#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RTS Analysis Engine (Unified)
- Reads incidents/*.md and incidents/*_DRAFT.md
- Extracts evidence pointers:
  - evidence_pack
  - run_url
  - snapshot_ref
  - snapshot_hash_sha256
  - python_script
- Classifies Evidence Level (0-2) automatically
- Writes analysis/index.md (GitHub Pages friendly)
"""

from __future__ import annotations

import re
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
INCIDENTS_DIR = ROOT / "incidents"
OUTPUT = ROOT / "analysis" / "index.md"


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------
# Parsing helpers
# ----------------------------

_FRONTMATTER_RE = re.compile(r"(?s)\A---\s*\n(.*?)\n---\s*\n")


def parse_frontmatter(text: str) -> Dict[str, str]:
    """
    Very small YAML-ish parser for 'key: value' pairs in frontmatter.
    (Good enough for RTS template; avoids external deps.)
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    block = m.group(1)
    out: Dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip()
        # normalize null-ish
        if v.lower() in ("null", "none", "pending", ""):
            v = ""
        # strip quotes
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        out[k] = v
    return out


def find_bullet_value(text: str, key: str) -> str:
    """
    Extracts either:
      - key: value
    or
      - key:
          value
    anywhere in the file.
    """
    # inline
    m = re.search(rf"(?m)^\s*[-*]\s*{re.escape(key)}\s*:\s*(.+?)\s*$", text)
    if m:
        return m.group(1).strip()

    # block style
    m = re.search(rf"(?m)^\s*[-*]\s*{re.escape(key)}\s*:\s*$", text)
    if m:
        # find next indented non-empty line
        after = text[m.end():]
        for line in after.splitlines():
            if not line.strip():
                continue
            if re.match(r"^\s{2,}\S", line):
                return line.strip()
            break
    return ""


def extract_fields(path: Path) -> Dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(text)

    # priority: frontmatter -> bullet values
    def get(key: str) -> str:
        return (fm.get(key) or find_bullet_value(text, key)).strip()

    return {
        "file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "schema_version": get("schema_version"),
        "evidence_level": get("evidence_level"),
        "analysis_status": get("analysis_status"),
        "evidence_pack": get("evidence_pack"),
        "run_url": get("run_url"),
        "snapshot_ref": get("snapshot_ref"),
        "snapshot_hash_sha256": get("snapshot_hash_sha256"),
        "python_script": get("python_script"),
    }


# ----------------------------
# Evidence Level (0-2)
# ----------------------------

def classify_level(fields: Dict[str, str]) -> int:
    """
    Level 0: no external reference
    Level 1: run_url or evidence_pack exists
    Level 2: snapshot_hash_sha256 exists (snapshot_ref expected)
    Level 3: reserved (multi-source corroboration)
    """
    if fields.get("snapshot_hash_sha256"):
        return 2
    if fields.get("run_url") or fields.get("evidence_pack"):
        return 1
    return 0


# ----------------------------
# Collection
# ----------------------------

def collect_incident_files() -> List[Path]:
    if not INCIDENTS_DIR.exists():
        return []
    files: List[Path] = []
    for p in INCIDENTS_DIR.glob("*.md"):
        if p.name.startswith("."):
            continue
        files.append(p)
    # include drafts if placed in other naming too (already *.md)
    return sorted(files, key=lambda x: x.name)


# ----------------------------
# Markdown output
# ----------------------------

def md_link(label: str, target: str) -> str:
    # target should be repo-relative path (or url)
    return f"[{label}]({target})"


def write_index(rows: List[Dict[str, str]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    generated_at = now_utc_iso()

    # header
    lines: List[str] = []
    lines.append("# RTS Analysis Index")
    lines.append("")
    lines.append(f"- generated_at_utc: `{generated_at}`")
    lines.append(f"- incidents_count: `{len(rows)}`")
    lines.append("")

    # summary counts by level
    c0 = sum(1 for r in rows if int(r["level"]) == 0)
    c1 = sum(1 for r in rows if int(r["level"]) == 1)
    c2 = sum(1 for r in rows if int(r["level"]) == 2)
    lines.append("## Evidence Level Summary")
    lines.append("")
    lines.append(f"- Level0: `{c0}`")
    lines.append(f"- Level1: `{c1}`")
    lines.append(f"- Level2: `{c2}`")
    lines.append("")
    lines.append("> Level2 means: snapshot_hash_sha256 exists (hash-of-snapshot).")
    lines.append("")

    # table
    lines.append("## Incidents")
    lines.append("")
    lines.append("| Incident file | Level | run_url | evidence_pack | snapshot_ref | snapshot_hash_sha256 | python_script |")
    lines.append("|---|---:|---|---|---|---|---|")

    for r in rows:
        f = r["file"]
        level = r["level"]

        run_url = r["run_url"]
        evidence_pack = r["evidence_pack"]
        snapshot_ref = r["snapshot_ref"]
        snapshot_hash = r["snapshot_hash_sha256"]
        python_script = r["python_script"]

        f_cell = md_link(Path(f).name, f.replace(" ", "%20"))

        run_cell = md_link("run", run_url) if run_url else ""
        pack_cell = md_link("pack", evidence_pack.replace(" ", "%20")) if evidence_pack else ""
        snap_cell = md_link("snap", snapshot_ref.replace(" ", "%20")) if snapshot_ref else ""
        hash_cell = f"`{snapshot_hash}`" if snapshot_hash else ""
        py_cell = md_link("script", python_script) if python_script else ""

        lines.append(f"| {f_cell} | {level} | {run_cell} | {pack_cell} | {snap_cell} | {hash_cell} | {py_cell} |")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This report is evidence-first. It does not infer causes beyond what is recorded.")
    lines.append("- Operator judgement remains final.")
    lines.append("")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    files = collect_incident_files()

    rows: List[Dict[str, str]] = []
    for p in files:
        fields = extract_fields(p)
        fields["level"] = str(classify_level(fields))
        fields["sha256"] = sha256_file(p)
        rows.append(fields)

    write_index(rows)
    print(f"[OK] analysis index written: {OUTPUT} (incidents={len(rows)})")


if __name__ == "__main__":
    main()
