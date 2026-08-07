from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .intake import SourceNote


@dataclass(frozen=True)
class CaptureRecord:
    capture_id: str
    source_path: str
    source_hash: str
    captured_at: str
    content_file: str


class CaptureStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.captures = self.root / "captures"
        self.index_path = self.root / "index.json"

    def _load_index(self) -> dict[str, list[dict[str, str]]]:
        if not self.index_path.exists():
            return {}
        with self.index_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_index(self, index: dict[str, list[dict[str, str]]]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temp = self.index_path.with_suffix(".tmp")
        temp.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(self.index_path)

    def capture(self, note: SourceNote) -> tuple[CaptureRecord, bool]:
        index = self._load_index()
        history = index.get(note.relative_path, [])
        for existing in history:
            if existing["source_hash"] == note.content_hash:
                return CaptureRecord(**existing), False

        version = len(history) + 1
        stable = note.content_hash[:16]
        capture_id = f"KBC-{stable}-V{version:04d}"
        capture_dir = self.captures / capture_id
        capture_dir.mkdir(parents=True, exist_ok=False)
        content_path = capture_dir / "source.md"
        content_path.write_bytes(note.content)
        record = CaptureRecord(
            capture_id=capture_id,
            source_path=note.relative_path,
            source_hash=note.content_hash,
            captured_at=datetime.now(timezone.utc).isoformat(),
            content_file=str(content_path.relative_to(self.root).as_posix()),
        )
        (capture_dir / "record.json").write_text(
            json.dumps(asdict(record), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        history.append(asdict(record))
        index[note.relative_path] = history
        self._write_index(index)
        return record, True

    def verify(self) -> list[str]:
        errors: list[str] = []
        for source_path, history in self._load_index().items():
            seen: set[str] = set()
            for item in history:
                capture_id = item["capture_id"]
                if capture_id in seen:
                    errors.append(f"duplicate capture id: {capture_id}")
                seen.add(capture_id)
                content = self.root / item["content_file"]
                if not content.exists():
                    errors.append(f"missing capture content for {source_path}: {content}")
        return errors
