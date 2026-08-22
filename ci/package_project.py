#!/usr/bin/env python3
"""Create content-identical Faxit Reborn packages for all supported platforms."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


PLATFORM_TARGETS = ("Windows", "LinuxServer", "WindowsServer")


def resolve_output(root: Path, output: Path) -> Path:
    return output.resolve() if output.is_absolute() else (root / output).resolve()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("dist/FaxitReborn.zip"))
    args = parser.parse_args()

    root = args.root.resolve()
    plugin = root / "FaxitReborn.uplugin"
    dataforge = root / "DataForge"
    config = root / "Config"
    for required in (plugin, dataforge, config):
        if not required.exists():
            raise SystemExit(f"missing package input: {required}")

    output = resolve_output(root, args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for platform in PLATFORM_TARGETS:
            archive.write(plugin, f"{platform}/{plugin.name}")
            for source_root in (dataforge, config):
                for path in sorted(source_root.rglob("*")):
                    if path.is_symlink():
                        raise SystemExit(f"symlinks are not allowed in release content: {path}")
                    if path.is_file() and path.name != "Alpakit.ini":
                        relative = path.relative_to(root).as_posix()
                        archive.write(path, f"{platform}/{relative}")
    print(f"created {output} ({output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
