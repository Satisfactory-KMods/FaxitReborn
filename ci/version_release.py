#!/usr/bin/env python3
"""Set plugin and pack versions to <year>.<quarter>.<CI run number>."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


PACK_VERSION = re.compile(r"^version:[^\r\n]*$", re.MULTILINE)
RELEASE_DEPENDENCIES = frozenset({"KDataForge", "KAPI", "KPrivateCodeLib", "KLib"})


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD") from error


def compute_version(build_number: int, release_date: date) -> str:
    if build_number < 1:
        raise ValueError("build number must be positive")
    quarter = ((release_date.month - 1) // 3) + 1
    return f"{release_date.year}.{quarter}.{build_number}"


def update_plugin(path: Path, version: str) -> None:
    try:
        descriptor: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read plugin descriptor {path}: {error}") from error
    if not isinstance(descriptor, dict):
        raise ValueError(f"plugin descriptor must be a JSON object: {path}")
    descriptor["Version"] = int(version.split(".", maxsplit=1)[0])
    descriptor["VersionName"] = version
    descriptor["SemVersion"] = version
    path.write_text(json.dumps(descriptor, indent="\t") + "\n", encoding="utf-8", newline="\n")


def update_pack(path: Path, version: str) -> None:
    try:
        manifest = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"cannot read pack manifest {path}: {error}") from error
    matches = PACK_VERSION.findall(manifest)
    if len(matches) != 1:
        raise ValueError(f"pack manifest must contain exactly one top-level version field: {path}")
    updated = PACK_VERSION.sub(f"version: {version}", manifest, count=1)
    path.write_text(updated, encoding="utf-8", newline="\n")


def blocked_release_dependencies(path: Path) -> list[str]:
    try:
        descriptor: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read plugin descriptor {path}: {error}") from error
    if not isinstance(descriptor, dict) or not isinstance(descriptor.get("Plugins"), list):
        raise ValueError(f"plugin descriptor requires Plugins sequence: {path}")
    versions = {
        plugin.get("Name"): plugin.get("SemVersion")
        for plugin in descriptor["Plugins"]
        if isinstance(plugin, dict) and isinstance(plugin.get("Name"), str)
    }
    return sorted(
        dependency
        for dependency in RELEASE_DEPENDENCIES
        if not isinstance(versions.get(dependency), str) or "9999.9.9" in versions[dependency]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--build-number", required=True, type=int)
    parser.add_argument("--date", type=parse_date, help="Override UTC date for deterministic verification")
    args = parser.parse_args()

    release_date = args.date or datetime.now(timezone.utc).date()
    try:
        version = compute_version(args.build_number, release_date)
        root = args.root.resolve()
        plugin_path = root / "FaxitReborn.uplugin"
        update_plugin(plugin_path, version)
        update_pack(root / "DataForge" / "pack.yml", version)
        blocked_dependencies = blocked_release_dependencies(plugin_path)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(f"version={version}")
    print(f"release_ready={'false' if blocked_dependencies else 'true'}")
    if blocked_dependencies:
        print(f"blocked_dependencies={','.join(blocked_dependencies)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
