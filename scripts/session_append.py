# scripts/session_append.py
import json, os, sys
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def month_dir(ts: str):
    return ts[:7]  # YYYY-MM

def day_str(ts: str):
    return ts[:10].replace("-", "")  # YYYYMMDD

def main():
    payload_path = sys.argv[1]  # JSON 1件（ファイル）で渡す
    with open(payload_path, "r", encoding="utf-8") as f:
        ev = json.load(f)

    ev.setdefault("ts", utc_now())
    yymm = month_dir(ev["ts"])
    yyyymmdd = day_str(ev["ts"])

    base = os.path.join("sessions", yymm)
    os.makedirs(base, exist_ok=True)

    raw_path = os.path.join(base, f"session_{yyyymmdd}.jsonl")
    with open(raw_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    # update index.json (light)
    index_path = os.path.join(base, "index.json")
    idx = {"month": yymm, "updated_at_utc": ev["ts"], "counts": {}, "latest": []}
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            idx = json.load(f)

    kind = ev.get("kind", "unknown")
    idx["counts"][kind] = int(idx["counts"].get(kind, 0)) + 1
    idx["updated_at_utc"] = ev["ts"]

    # keep last 30 event summaries
    summary = {k: ev.get(k) for k in ["ts","kind","workflow","run_id","status","commit","note"] if k in ev}
    idx["latest"] = (idx.get("latest", []) + [summary])[-30:]

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
