from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from asset_manifest.core import (
    AssetManifestError,
    create_snapshot,
    derive_indexes,
    diff_snapshots,
    load_current_snapshot,
    rebuild_manifest,
    reindex,
    validate_snapshot,
    verify,
)


class AssetManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.seed = json.loads((cls.repo_root / "asset_manifest/snapshots/v001.json").read_text(encoding="utf-8"))

    def isolated_root(self) -> Path:
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp, ignore_errors=True)
        shutil.copytree(self.repo_root / "asset_manifest", temp / "asset_manifest")
        return temp

    def test_seed_is_valid_and_represents_all_repositories(self) -> None:
        validate_snapshot(self.seed)
        names = {repo["repository"] for repo in self.seed["repositories"]}
        self.assertEqual(19, len(names))
        self.assertIn("nobutakayamauchi/RTS", names)
        self.assertIn("nobutakayamauchi/RTS-minicompany", names)
        self.assertIn("nobutakayamauchi/rts-lite", names)

    def test_indexes_are_deterministic(self) -> None:
        self.assertEqual(derive_indexes(self.seed), derive_indexes(deepcopy(self.seed)))

    def test_duplicate_asset_id_is_rejected(self) -> None:
        broken = deepcopy(self.seed)
        broken["assets"].append(deepcopy(broken["assets"][0]))
        with self.assertRaisesRegex(AssetManifestError, "duplicate asset_id"):
            validate_snapshot(broken)

    def test_conflicting_canonical_ownership_is_rejected(self) -> None:
        broken = deepcopy(self.seed)
        clone = deepcopy(broken["assets"][0])
        clone["asset_id"] = "RTS-AM-A9999"
        clone["repository"] = "nobutakayamauchi/RTS-AGE"
        broken["assets"].append(clone)
        with self.assertRaisesRegex(AssetManifestError, "conflicting canonical ownership"):
            validate_snapshot(broken)

    def test_private_locator_leak_is_rejected(self) -> None:
        broken = deepcopy(self.seed)
        private = next(asset for asset in broken["assets"] if asset["repository"] == "nobutakayamauchi/RTS-minicompany")
        private["locator"] = "customer/cases/real-client.json"
        with self.assertRaisesRegex(AssetManifestError, "logical: locator"):
            validate_snapshot(broken)

    def test_restricted_asset_is_rejected(self) -> None:
        broken = deepcopy(self.seed)
        broken["assets"][0]["sensitivity"] = "RESTRICTED"
        broken["assets"][0]["locator"] = "logical:redacted"
        with self.assertRaisesRegex(AssetManifestError, "restricted assets"):
            validate_snapshot(broken)

    def test_direct_unknown_license_is_rejected(self) -> None:
        broken = deepcopy(self.seed)
        broken["assets"][0]["license_status"] = "UNKNOWN"
        with self.assertRaisesRegex(AssetManifestError, "DIRECT reuse"):
            validate_snapshot(broken)

    def test_missing_repository_is_rejected(self) -> None:
        broken = deepcopy(self.seed)
        broken["assets"][0]["repository"] = "nobutakayamauchi/missing"
        with self.assertRaisesRegex(AssetManifestError, "unknown repository"):
            validate_snapshot(broken)

    def test_invalid_enum_is_rejected(self) -> None:
        broken = deepcopy(self.seed)
        broken["assets"][0]["reuse_mode"] = "COPY_ANYTHING"
        with self.assertRaisesRegex(AssetManifestError, "invalid reuse_mode"):
            validate_snapshot(broken)

    def test_append_only_create_and_diff(self) -> None:
        root = self.isolated_root()
        input_snapshot = deepcopy(self.seed)
        for field in ("schema_version", "snapshot_version"):
            input_snapshot.pop(field, None)
        input_snapshot["generated_at"] = "2026-07-24T04:00:00Z"
        input_snapshot["known_gaps"].append("second snapshot")
        source = root / "input.json"
        source.write_text(json.dumps(input_snapshot, ensure_ascii=False), encoding="utf-8")
        created = create_snapshot(root, source)
        self.assertEqual(2, created["snapshot_version"])
        self.assertTrue((root / "asset_manifest/snapshots/v001.json").exists())
        self.assertTrue((root / "asset_manifest/snapshots/v002.json").exists())
        delta = diff_snapshots(root, 1, 2)
        self.assertEqual([], delta["assets"]["added"])
        self.assertEqual([], delta["repositories"]["changed"])
        self.assertEqual(2, load_current_snapshot(root)["snapshot_version"])
        self.assertEqual([], verify(root))

    def test_stale_pointer_is_rejected(self) -> None:
        root = self.isolated_root()
        pointer = json.loads((root / "asset_manifest/snapshots/current.json").read_text(encoding="utf-8"))
        pointer["path"] = "asset_manifest/snapshots/v999.json"
        (root / "asset_manifest/snapshots/current.json").write_text(json.dumps(pointer), encoding="utf-8")
        rebuild_manifest(root)
        self.assertTrue(any("pointer path mismatch" in error for error in verify(root)))

    def test_stale_index_is_rejected(self) -> None:
        root = self.isolated_root()
        assets_path = root / "asset_manifest/index/assets.json"
        data = json.loads(assets_path.read_text(encoding="utf-8"))
        data["count"] = 0
        assets_path.write_text(json.dumps(data), encoding="utf-8")
        rebuild_manifest(root)
        self.assertIn("stale index: asset_manifest/index/assets.json", verify(root))

    def test_manifest_mismatch_is_rejected(self) -> None:
        root = self.isolated_root()
        readme = root / "asset_manifest/README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
        self.assertTrue(any("hash mismatch: asset_manifest/README.md" == error for error in verify(root)))

    def test_reindex_restores_indexes_and_manifest(self) -> None:
        root = self.isolated_root()
        (root / "asset_manifest/index/assets.json").write_text("{}\n", encoding="utf-8")
        reindex(root)
        self.assertEqual([], verify(root))


if __name__ == "__main__":
    unittest.main()
