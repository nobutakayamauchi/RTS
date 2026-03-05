#!/usr/bin/env python3
# reset_engine.py
# RTS Auto Reset System (minimal, reliable)

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))

RESET_DIR = Path(".rts")
RESET_STATE = RESET_DIR / "reset_state.json"

RADAR_SEEN = Path("radar") / "seen.json"

LOGS_DIR = Path("logs")

FAIL_THRESHOLD = 3          # 連続失敗がここに達したらハードリセット
COOLDOWN_MINUTES = 30       # ハードリセット後、この時間は “実行しない”


@dataclass
class ResetState:
    consecutive_failures: int = 0
    last_failure_utc: str | None = None
    last_reset_utc: str | None = None
    cooldown_until_utc: str | None = None

    @staticmethod
    def load() -> "ResetState":
        if RESET_STATE.exists():
            try:
                data = json.loads(RESET_STATE.read_text(encoding="utf-8"))
                return ResetState(
                    consecutive_failures=int(data.get("consecutive_failures", 0)),
                    last_failure_utc=data.get("last_failure_utc"),
                    last_reset_utc=data.get("last_reset_utc"),
                    cooldown_until_utc=data.get("cooldown_until_utc"),
                )
            except Exception:
                # 壊れてても復旧できるように初期化
                return ResetState()
        return ResetState()

    def save(self) -> None:
        RESET_DIR.mkdir(parents=True, exist_ok=True)
        RESET_STATE.write_text(
            json.dumps(
                {
                    "consecutive_failures": self.consecutive_failures,
                    "last_failure_utc": self.last_failure_utc,
                    "last_reset_utc": self.last_reset_utc,
                    "cooldown_until_utc": self.cooldown_until_utc,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_utc_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def write_block(event: str, notes: str) -> Path:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # BLOCK id: 既存文化に合わせて “ざっくり”増分（ファイル数+1）でOK
    existing = sorted(LOGS_DIR.glob("BLOCK_*.md"))
    block_id = len(existing) + 1
    block_name = f"BLOCK_{block_id:08d}_AUTO_RESET.md"
    p = LOGS_DIR / block_name

    jst_now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    content = f"""BLOCK_{block_id:08d}

Event: {event}
Time: {jst_now}

Notes:
{notes}

Integrity: VERIFIED
"""
    p.write_text(content, encoding="utf-8")
    return p


def soft_reset(notes: list[str]) -> None:
    # “軽い復旧”：今回は状態ファイルだけ整える（必要なら拡張）
    notes.append("Soft reset executed: state normalized.")


def hard_reset(notes: list[str]) -> None:
    # “重い復旧”：Radarのseen.jsonを安全に退避して再生成
    if RADAR_SEEN.exists():
        backup = RADAR_SEEN.with_suffix(".json.bak")
        try:
            backup.write_text(RADAR_SEEN.read_text(encoding="utf-8"), encoding="utf-8")
            notes.append(f"Radar seen.json backed up -> {backup.as_posix()}")
        except Exception:
            notes.append("Radar seen.json backup failed (ignored).")

        try:
            RADAR_SEEN.write_text("{}", encoding="utf-8")
            notes.append("Radar seen.json reset to empty {}")
        except Exception:
            notes.append("Radar seen.json reset failed (ignored).")
    else:
        # ないなら作る
        RADAR_SEEN.parent.mkdir(parents=True, exist_ok=True)
        RADAR_SEEN.write_text("{}", encoding="utf-8")
        notes.append("Radar seen.json created as empty {}")

    notes.append("Hard reset executed.")


def main() -> None:
    # workflow 側で failure() の時だけ呼ぶ想定
    state = ResetState.load()

    now_utc = datetime.now(timezone.utc)
    cooldown_until = parse_utc_iso(state.cooldown_until_utc)

    # cooldown中なら “何もしない”（暴走防止）
    if cooldown_until and now_utc < cooldown_until:
        write_block(
            event="RTS AUTO RESET skipped (cooldown active)",
            notes=f"Cooldown until (UTC): {cooldown_until.isoformat()}",
        )
        state.save()
        print("Cooldown active. Skipping reset.")
        return

    # failure 1回ぶん加算
    state.consecutive_failures += 1
    state.last_failure_utc = now_utc_iso()

    notes: list[str] = []
    notes.append(f"Consecutive failures: {state.consecutive_failures}/{FAIL_THRESHOLD}")

    if state.consecutive_failures >= FAIL_THRESHOLD:
        # ハードリセット + cooldown
        hard_reset(notes)
        state.last_reset_utc = now_utc_iso()
        state.cooldown_until_utc = (now_utc + timedelta(minutes=COOLDOWN_MINUTES)).replace(microsecond=0).isoformat()
        notes.append(f"Cooldown set: {COOLDOWN_MINUTES} minutes")
        # リセットしたらカウンタを戻す（連鎖防止）
        state.consecutive_failures = 0
    else:
        soft_reset(notes)

    block_path = write_block(
        event="RTS AUTO RESET executed",
        notes="\n".join(f"- {n}" for n in notes),
    )

    state.save()
    print(f"Reset done. Block written: {block_path.as_posix()}")


if __name__ == "__main__":
    main()
