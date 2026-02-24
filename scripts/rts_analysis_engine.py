import os
import json
import hashlib
from datetime import datetime, timezone, timedelta

ROOT = os.getcwd()

EVIDENCE_PACK_DIR = "incidents/evidence_packs"
SNAPSHOT_DIR = "incidents/evidence_snapshots"
OUTPUT = "analysis/index.md"

JST = timezone(timedelta(hours=9))


def now_utc():

    return datetime.now(timezone.utc).replace(microsecond=0)


def sha256_file(path):

    h = hashlib.sha256()

    with open(path,"rb") as f:

        while True:

            chunk = f.read(8192)

            if not chunk:

                break

            h.update(chunk)

    return h.hexdigest()


# ---------- Evidence Level ----------

def classify_evidence_level(pack_text):

    if "snapshot_hash_sha256" in pack_text:

        return 2

    if "run=" in pack_text:

        return 1

    return 0


# ---------- Analysis ----------

def analyze_pack(path):

    with open(path,"r",encoding="utf-8") as f:

        text = f.read()

    level = classify_evidence_level(text)

    return {

        "file":path,

        "level":level,

        "hash":sha256_file(path),

        "analysis_time":now_utc().isoformat()

    }


# ---------- Collector ----------

def collect_packs():

    results=[]

    if not os.path.exists(EVIDENCE_PACK_DIR):

        return results

    for name in sorted(os.listdir(EVIDENCE_PACK_DIR)):

        if not name.endswith(".md"):

            continue

        path=os.path.join(EVIDENCE_PACK_DIR,name)

        results.append(analyze_pack(path))

    return results


# ---------- Output ----------

def write_index(results):

    os.makedirs("analysis",exist_ok=True)

    with open(OUTPUT,"w",encoding="utf-8") as f:

        f.write("# RTS Analysis Index\n\n")

        f.write(f"generated_at_utc: {now_utc().isoformat()}\n\n")

        for r in results:

            f.write("## Evidence\n")

            f.write(f"- file: {r['file']}\n")

            f.write(f"- evidence_hash: {r['hash']}\n")

            f.write(f"- evidence_level: {r['level']}\n")

            f.write("\n")

            f.write("## Analysis\n")

            f.write("- rule: evidence-only counter inspection\n")

            f.write(f"- analyzed_at: {r['analysis_time']}\n")

            f.write("\n")

            f.write("## Conclusion\n")

            f.write("- operator judgement required\n")

            f.write("\n---\n\n")


# ---------- Main ----------

def main():

    results = collect_packs()

    write_index(results)

    print(f"[OK] analyzed {len(results)} packs")


if __name__=="__main__":

    main()
