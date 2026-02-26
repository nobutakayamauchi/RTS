# scripts/session_rollup.py
import json, os, sys
from glob import glob

def main():
    month = sys.argv[1]  # YYYY-MM
    base = os.path.join("sessions", month)
    index_json = os.path.join(base, "index.json")
    if not os.path.exists(index_json):
        print("no index.json:", index_json)
        return

    with open(index_json, "r", encoding="utf-8") as f:
        idx = json.load(f)

    md = []
    md.append(f"# RTS Sessions — {month}")
    md.append("")
    md.append(f"- updated_at_utc: `{idx.get('updated_at_utc')}`")
    md.append("")
    md.append("## Counts")
    for k,v in sorted(idx.get("counts", {}).items(), key=lambda x: (-x[1], x[0])):
        md.append(f"- `{k}`: **{v}**")
    md.append("")
    md.append("## Latest (tail)")
    for ev in idx.get("latest", []):
        md.append(f"- `{ev.get('ts')}` `{ev.get('kind')}`"
                  f" workflow={ev.get('workflow','-')} run={ev.get('run_id','-')}"
                  f" status={ev.get('status','-')} commit={ev.get('commit','-')}"
                  f" — {ev.get('note','')}".rstrip())
    md.append("")
    md.append("## Raw ledgers")
    for p in sorted(glob(os.path.join(base, "session_*.jsonl"))):
        md.append(f"- `{os.path.basename(p)}`")

    out = os.path.join(base, "index.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

if __name__ == "__main__":
    main()
