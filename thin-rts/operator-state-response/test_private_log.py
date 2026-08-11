import json
import os
from pathlib import Path
import stat
import tempfile
import unittest

from private_log import PrivateLogError, REPO_ROOT, append_private_record, validate_private_path


class PrivateLogTests(unittest.TestCase):
    def test_public_repo_path_is_rejected(self):
        with self.assertRaises(PrivateLogError):
            validate_private_path(REPO_ROOT / "operator-health.jsonl")

    def test_private_log_is_append_only_jsonl_and_owner_only(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "state.jsonl"
            append_private_record({"schema": "operator-state-response/v0", "x": 1}, target)
            append_private_record({"schema": "operator-state-response/v0", "x": 2}, target)
            rows = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["x"] for row in rows], [1, 2])
            self.assertTrue(all("logged_at" in row for row in rows))
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()
