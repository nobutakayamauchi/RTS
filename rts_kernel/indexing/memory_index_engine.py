#!/usr/bin/env python3
# memory_index.py
# RTS Memory Index Engine (searchable memory)

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(".")
LOGS_DIR = ROOT / "logs"
INCIDENTS_DIR = ROOT / "incidents"
MEMORY_DIR = ROOT / "memory"

INDEX_JSON = MEMORY_DIR / "index.json"
INDEX_MD = MEMORY_DIR / "index.md"

UTC = timezone.utc

# 日本語も雑に拾うため「英数字+_」と「ひらがな/カタカナ/漢字」もトークン化
TOKEN_RE = re.compile(r"[A-Za-z0-9_]{2,}|[ぁ-んァ-ン一-龥]{2,}")


@dataclass
class Doc:
    doc_id: str
    path: str
    kind: str  # log | incident | other
    title: str
    time: Optional[str]  # ISO
    event: Optional[str]
    url: Optional[str]
    snippet: str
    tokens: List[str]


def now_utc_iso() -> str:
    return datetime.now(UTC).isoformat()


def safe_read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def extract_first_url(text: str) -> Optional[str]:
    m = re.search(r"(https?://\S+)", text)
    return m.group(1).rstrip(").,]") if m else None


def extract_fields_from_log(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Try to parse common RTS log block format:
      Event: ...
      Time: ...
      Date: ...
      Notes: ...
    Return (event, time_iso, title_guess)
    """
    event = None
    time_iso = None
    title_guess = None

    # Event:
    m = re.search(r"^Event:\s*(.+)$", text, re.MULTILINE)
    if m:
        event = m.group(1).strip()
        title_guess = event

    # Time: 2026-... or JST string; keep as raw if not ISO
    m = re.search(r"^Time:\s*(.+)$", text, re.MULTILINE)
    if m:
        raw = m.group(1).strip()
        # best-effort: if already ISO-ish
        time_iso = raw

    # Date: 2026-02-23 JST -> store as raw
    if not time_iso:
        m = re.search(r"^Date:\s*(.+)$", text, re.MULTILINE)
        if m:
            time_iso = m.group(1).strip()

    return event, time_iso, title_guess


def extract_fields_from_incident(text: str, fallback_title: str) -> Tuple[str, Optional[str]]:
    """
    Incidents often contain: Title: ... or first heading line.
    """
    title = fallback_title
    m = re.search(r"^Title:\s*(.+)$", text, re.MULTILINE)
    if m:
        title = m.group(1).strip()
    else:
        # first markdown heading
        m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if m:
            title = m.group(1).strip()
    url = extract_first_url(text)
    return title, url


def tokenize(text: str) -> List[str]:
    toks = TOKEN_RE.findall(text)
    # 正規化（小文字化できる英字だけ）
    out = []
    for t in toks:
        if re.fullmatch(r"[A-Za-z0-9_]{2,}", t):
            out.append(t.lower())
        else:
            out.append(t)
    # 重複削除（順序保持）
    seen = set()
    uniq = []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def make_snippet(text: str, max_len: int = 180) -> str:
    s = re.sub(r"\s+", " ", text).strip()
    if len(s) <= max_len:
        return s
    return s[:max_len] + "…"


def build_docs() -> List[Doc]:
    docs: List[Doc] = []

    # logs
    if LOGS_DIR.exists():
        for p in sorted(LOGS_DIR.glob("*.md")):
            text = safe_read_text(p)
            event, time_iso, title_guess = extract_fields_from_log(text)
            url = extract_first_url(text)
            title = title_guess or p.name
            doc_id = f"log:{p.name}"
            toks = tokenize(text)
            docs.append(
                Doc(
                    doc_id=doc_id,
                    path=str(p.as_posix()),
                    kind="log",
                    title=title,
                    time=time_iso,
                    event=event,
                    url=url,
                    snippet=make_snippet(text),
                    tokens=toks,
                )
            )

    # incidents
    if INCIDENTS_DIR.exists():
        for p in sorted(INCIDENTS_DIR.glob("*.md")):
            text = safe_read_text(p)
            title, url = extract_fields_from_incident(text, fallback_title=p.name)
            doc_id = f"incident:{p.name}"
            toks = tokenize(text)
            docs.append(
                Doc(
                    doc_id=doc_id,
                    path=str(p.as_posix()),
                    kind="incident",
                    title=title,
                    time=None,
                    event=None,
                    url=url,
                    snippet=make_snippet(text),
                    tokens=toks,
                )
            )

    return docs


def build_inverted_index(docs: List[Doc]) -> Dict[str, List[str]]:
    inv: Dict[str, List[str]] = {}
    for d in docs:
        for t in d.tokens:
            inv.setdefault(t, []).append(d.doc_id)
    return inv


def write_index_files(payload: Dict[str, Any]) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # human-friendly summary
    docs = payload["docs"]
    lines = []
    lines.append("# RTS MEMORY INDEX")
    lines.append("")
    lines.append(f"- generated_utc: `{payload['generated_utc']}`")
    lines.append(f"- docs: `{len(docs)}`")
    lines.append("")
    lines.append("## Latest Logs")
    lines.append("")
    # logs only, take last 20 by filename sort (works with BLOCK_*)
    logs = [d for d in docs if d["kind"] == "log"]
    for d in logs[-20:][::-1]:
        lines.append(f"- **{d['title']}**  (`{d['path']}`)")
        if d.get("time"):
            lines.append(f"  - time: {d['time']}")
        if d.get("event"):
            lines.append(f"  - event: {d['event']}")
        if d.get("url"):
            lines.append(f"  - url: {d['url']}")
        lines.append(f"  - snippet: {d['snippet']}")
    lines.append("")
    lines.append("## Incidents")
    lines.append("")
    inc = [d for d in docs if d["kind"] == "incident"]
    for d in inc[-20:][::-1]:
        lines.append(f"- **{d['title']}** (`{d['path']}`)")
        if d.get("url"):
            lines.append(f"  - url: {d['url']}")
        lines.append(f"  - snippet: {d['snippet']}")
    lines.append("")

    INDEX_MD.write_text("\n".join(lines), encoding="utf-8")


def load_index() -> Optional[Dict[str, Any]]:
    if not INDEX_JSON.exists():
        return None
    try:
        return json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    except Exception:
        return None


def search(index: Dict[str, Any], query: str, limit: int = 10) -> List[Dict[str, Any]]:
    docs_by_id = {d["doc_id"]: d for d in index["docs"]}
    inv = index["inverted_index"]

    q_tokens = tokenize(query)
    if not q_tokens:
        return []

    # AND検索（全部含むdocのみ）
    hits: Optional[set] = None
    for t in q_tokens:
        ids = set(inv.get(t, []))
        hits = ids if hits is None else (hits & ids)

    if not hits:
        return []

    # スコア：一致トークン数 + kind重み（log優先）
    scored = []
    for doc_id in hits:
        d = docs_by_id.get(doc_id)
        if not d:
            continue
        score = 0
        for t in q_tokens:
            if doc_id in inv.get(t, []):
                score += 1
        if d["kind"] == "log":
            score += 1
        scored.append((score, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:limit]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true", help="rebuild index files")
    ap.add_argument("--q", type=str, default=None, help="search query")
    ap.add_argument("--limit", type=int, default=10, help="search results limit")
    args = ap.parse_args()

    if args.rebuild or args.q is None:
        docs = build_docs()
        inv = build_inverted_index(docs)
        payload = {
            "generated_utc": now_utc_iso(),
            "docs": [asdict(d) for d in docs],
            "inverted_index": inv,
        }
        write_index_files(payload)
        print(f"[OK] Memory index built: {INDEX_JSON} ({len(docs)} docs)")

    if args.q:
        idx = load_index()
        if not idx:
            print("[WARN] index.json not found. Run with --rebuild first.")
            return
        hits = search(idx, args.q, limit=args.limit)
        print(f"[HITS] {len(hits)}")
        for d in hits:
            print(f"- {d['kind']} | {d['title']} | {d['path']}")
            if d.get("url"):
                print(f"  url: {d['url']}")
            print(f"  {d['snippet']}")


if __name__ == "__main__":
    main()
