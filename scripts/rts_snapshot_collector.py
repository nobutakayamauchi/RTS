import os
import re
import hashlib
import urllib.request
from datetime import datetime, timezone, timedelta

ROOT = os.getcwd()

PACK_DIR = "incidents/evidence_packs"
SNAPSHOT_DIR = "incidents/evidence_snapshots"

JST = timezone(timedelta(hours=9))


def now_jst():

    return datetime.now(JST).strftime("%Y%m%d_%H%M%S")


def sha256_bytes(data: bytes):

    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def extract_urls(text):

    return re.findall(r"https?://[^\s)]+", text)


def download(url):

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "RTS-SnapshotCollector"
        }
    )

    with urllib.request.urlopen(req, timeout=20) as r:

        return r.read()


def save_snapshot(content: bytes):

    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    ts = now_jst()

    filename = f"SNAP_{ts}.bin"

    path = os.path.join(SNAPSHOT_DIR, filename)

    with open(path,"wb") as f:

        f.write(content)

    return path


def append_frontmatter(pack_path, snapshot_path, snapshot_hash):

    with open(pack_path,"r",encoding="utf-8") as f:

        lines = f.readlines()

    if not lines[0].startswith("---"):

        return

    insert_index = None

    for i,l in enumerate(lines):

        if l.strip() == "---" and i != 0:

            insert_index = i

            break

    if insert_index is None:

        return

    insert = [

        f"snapshot_ref: {snapshot_path}\n",

        f"snapshot_hash_sha256: {snapshot_hash}\n",

        f"retrieved_at: {datetime.now(JST).isoformat()}\n"

    ]

    new_lines = (

        lines[:insert_index]
        + insert
        + lines[insert_index:]
    )

    with open(pack_path,"w",encoding="utf-8") as f:

        f.writelines(new_lines)


def process_pack(pack):

    with open(pack,"r",encoding="utf-8") as f:

        text = f.read()

    urls = extract_urls(text)

    if not urls:

        return

    url = urls[0]

    try:

        data = download(url)

    except Exception as e:

        print("download fail",url,e)

        return

    snapshot_path = save_snapshot(data)

    h = sha256_bytes(data)

    append_frontmatter(pack,snapshot_path,h)

    print("snapshot saved:",snapshot_path)


def main():

    if not os.path.exists(PACK_DIR):

        return

    for name in os.listdir(PACK_DIR):

        if not name.endswith(".md"):

            continue

        process_pack(os.path.join(PACK_DIR,name))


if __name__ == "__main__":

    main()
