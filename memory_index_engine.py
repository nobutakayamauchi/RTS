#!/usr/bin/env python3
# RTS Memory Index Engine

from pathlib import Path
import json
from datetime import datetime, timezone

SCAN_DIRS = [
    "logs",
    "incidents",
    "radar",
    "evolution"
]

MEMORY_DIR = Path("memory")
INDEX_FILE = MEMORY_DIR / "MEMORY_INDEX.json"


def collect_files():

    collected = []

    for d in SCAN_DIRS:

        path = Path(d)

        if not path.exists():
            continue

        for file in path.glob("**/*.md"):

            try:

                stat = file.stat()

                collected.append({

                    "path": str(file),

                    "size": stat.st_size,

                    "modified_utc":
                    datetime.fromtimestamp(
                        stat.st_mtime,
                        timezone.utc
                    ).isoformat()

                })

            except Exception:
                continue

    return collected


def main():

    MEMORY_DIR.mkdir(exist_ok=True)

    index = {

        "generated_utc":
        datetime.now(timezone.utc).isoformat(),

        "total_files": 0,

        "entries": []

    }

    files = collect_files()

    index["total_files"] = len(files)
    index["entries"] = files

    INDEX_FILE.write_text(

        json.dumps(
            index,
            indent=2,
            ensure_ascii=False
        ),

        encoding="utf-8"

    )

    print(
        f"Memory index updated: {len(files)} files"
    )


if __name__ == "__main__":
    main()
