#!/usr/bin/env python3
"""Minimal verifier for Protect Frame v0.1 scaffold.

Uses PyYAML when available; otherwise falls back to a tiny parser that supports
this scaffold subset (top-level mapping with list entries and scalar/list fields).
"""

from __future__ import annotations

from pathlib import Path

try:  # pragma: no cover - depends on environment
    import yaml
except Exception:  # pragma: no cover - intentional fallback
    yaml = None

REQUIRED_FILES = {
    "docs/security/PROTECT_FRAME_v0.1.md": None,
    "security/asset_registry.yaml": "assets",
    "security/secret_scope_registry.yaml": "secrets",
    "security/trust_zones.yaml": "zones",
}

REQUIRED_ENTRY_KEYS = {
    "security/asset_registry.yaml": {
        "asset_id",
        "category",
        "criticality",
        "owner",
        "notes",
        "zone",
    },
    "security/secret_scope_registry.yaml": {
        "secret_id",
        "secret_type",
        "scope",
        "zone",
        "rotation_required",
        "max_lifetime",
        "usage_context",
        "blast_radius",
        "status",
    },
    "security/trust_zones.yaml": {
        "zone_id",
        "description",
        "allowed_assets",
        "forbidden_crossings",
        "notes",
    },
}

ALLOWED_CRITICALITY = {"critical", "high", "medium"}
ALLOWED_BLAST_RADIUS = {"high", "medium", "low"}
ALLOWED_SECRET_STATUS = {"active", "review_required", "disabled"}


def _parse_scalar(value: str):
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "~"}:
        return None
    return value


def _simple_yaml_load(text: str):
    lines = [ln.rstrip("\n") for ln in text.splitlines()]
    filtered = [ln for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]
    if not filtered:
        return {}

    first = filtered[0].strip()
    if not first.endswith(":"):
        raise ValueError("top-level key must end with ':'")

    top_key = first[:-1]
    root = {top_key: []}
    entries = root[top_key]
    current_entry: dict | None = None
    current_list_key: str | None = None

    for raw_line in filtered[1:]:
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()

        if indent == 2 and stripped.startswith("- "):
            body = stripped[2:]
            if ": " not in body:
                raise ValueError(f"entry start must be 'key: value': {raw_line}")
            key, value = body.split(": ", 1)
            current_entry = {key: _parse_scalar(value)}
            entries.append(current_entry)
            current_list_key = None
            continue

        if current_entry is None:
            raise ValueError(f"line appears before first entry: {raw_line}")

        if indent == 4 and ": " in stripped:
            key, value = stripped.split(": ", 1)
            current_entry[key] = _parse_scalar(value)
            current_list_key = None
            continue

        if indent == 4 and stripped.endswith(":"):
            key = stripped[:-1]
            current_entry[key] = []
            current_list_key = key
            continue

        if indent == 6 and stripped.startswith("- "):
            if current_list_key is None:
                raise ValueError(f"list item without list key: {raw_line}")
            current_entry[current_list_key].append(_parse_scalar(stripped[2:]))
            continue

        raise ValueError(f"unsupported YAML structure: {raw_line}")

    return root


def _load_yaml(file_path: Path):
    text = file_path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text)
    return _simple_yaml_load(text)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    errors: list[str] = []
    loaded: dict[str, dict] = {}

    for relative_path in REQUIRED_FILES:
        file_path = repo_root / relative_path
        if not file_path.exists():
            errors.append(f"missing required file: {relative_path}")

    for relative_path, top_key in REQUIRED_FILES.items():
        if top_key is None:
            continue

        file_path = repo_root / relative_path
        if not file_path.exists():
            continue

        try:
            data = _load_yaml(file_path)
        except Exception as exc:
            errors.append(f"invalid YAML in {relative_path}: {exc}")
            continue

        if not isinstance(data, dict):
            errors.append(f"{relative_path} must load as a YAML mapping")
            continue

        if top_key not in data:
            errors.append(f"{relative_path} is missing top-level key '{top_key}'")
            continue

        entries = data[top_key]
        if not isinstance(entries, list):
            errors.append(f"{relative_path}:{top_key} must be a list")
            continue

        required_keys = REQUIRED_ENTRY_KEYS[relative_path]
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(
                    f"{relative_path}:{top_key}[{index}] must be a mapping entry"
                )
                continue

            missing = sorted(required_keys - set(entry.keys()))
            if missing:
                errors.append(
                    f"{relative_path}:{top_key}[{index}] missing keys: {', '.join(missing)}"
                )

        loaded[relative_path] = data

    zones_data = loaded.get("security/trust_zones.yaml", {}).get("zones", [])
    known_zones = {
        zone.get("zone_id")
        for zone in zones_data
        if isinstance(zone, dict) and isinstance(zone.get("zone_id"), str)
    }

    for index, zone in enumerate(zones_data):
        if not isinstance(zone, dict):
            continue
        for list_key in ("allowed_assets", "forbidden_crossings"):
            if not isinstance(zone.get(list_key), list):
                errors.append(
                    f"security/trust_zones.yaml:zones[{index}].{list_key} must be a list"
                )

    assets = loaded.get("security/asset_registry.yaml", {}).get("assets", [])
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            continue

        criticality = str(asset.get("criticality", "")).strip()
        if criticality not in ALLOWED_CRITICALITY:
            errors.append(
                "security/asset_registry.yaml:assets"
                f"[{index}] invalid criticality '{criticality}'"
            )

        zone = str(asset.get("zone", "")).strip()
        if zone and zone not in known_zones:
            errors.append(
                f"security/asset_registry.yaml:assets[{index}] zone '{zone}' is undefined"
            )

    secrets = loaded.get("security/secret_scope_registry.yaml", {}).get("secrets", [])
    for index, secret in enumerate(secrets):
        if not isinstance(secret, dict):
            continue

        zone = str(secret.get("zone", "")).strip()
        if zone and zone not in known_zones:
            errors.append(
                "security/secret_scope_registry.yaml:secrets"
                f"[{index}] zone '{zone}' is undefined"
            )

        blast_radius = str(secret.get("blast_radius", "")).strip()
        if blast_radius not in ALLOWED_BLAST_RADIUS:
            errors.append(
                "security/secret_scope_registry.yaml:secrets"
                f"[{index}] invalid blast_radius '{blast_radius}'"
            )

        status = str(secret.get("status", "")).strip()
        if status not in ALLOWED_SECRET_STATUS:
            errors.append(
                "security/secret_scope_registry.yaml:secrets"
                f"[{index}] invalid status '{status}'"
            )

        max_lifetime = str(secret.get("max_lifetime", "")).strip()
        if not max_lifetime:
            errors.append(
                "security/secret_scope_registry.yaml:secrets"
                f"[{index}] max_lifetime must not be empty"
            )

    if errors:
        print("[FAIL] Protect Frame verification failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("[OK] Protect Frame v0.1 verification succeeded with v0.2 checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
