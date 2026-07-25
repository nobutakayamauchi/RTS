"""Update the governed-loop advisory target for the assessed ledger candidate.

Temporary helper; removed before merge.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "tests" / "test_governed_loop.py"
text = path.read_text(encoding="utf-8")
old = '        self.assertEqual(loop["recommendation_item_id"], "RTS-FRZ-000003")\n'
new = '        self.assertEqual(loop["recommendation_item_id"], "RTS-FRZ-000009")\n'
if text.count(old) != 1:
    raise RuntimeError("expected governed-loop advisory assertion not found exactly once")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
