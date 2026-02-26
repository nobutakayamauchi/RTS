# scripts/session_artifact_pack.py
import os, sys, hashlib, zipfile
from glob import glob

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    month = sys.argv[1]  # YYYY-MM
    base = os.path.join("sessions", month)
    raw_files = sorted(glob(os.path.join(base, "session_*.jsonl")))
    if not raw_files:
        print("no raw files")
        return

    zip_path = os.path.join(base, f"sessions_{month}.zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for f in raw_files:
            z.write(f, arcname=os.path.join(month, os.path.basename(f)))

    # write checksums
    lines = []
    for f in raw_files + [zip_path]:
        lines.append(f"{sha256_file(f)}  {os.path.relpath(f)}")
    out = os.path.join(base, "checksums.sha256")
    with open(out, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")

    print("packed:", zip_path)

if __name__ == "__main__":
    main()
