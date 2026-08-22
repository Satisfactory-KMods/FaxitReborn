#!/usr/bin/env python3
"""Validate and copy Changelog.md with a Discord announcement first line."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


VERSION = re.compile(r"^\d{4}\.[1-4]\.\d+$")


def render_changelog(source: str, version: str) -> str:
    if not VERSION.fullmatch(version):
        raise ValueError("version must use <year>.<quarter>.<build-number>")
    normalized = source.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.splitlines()
    if not lines or not lines[0].strip():
        raise ValueError("Changelog.md first line must be the Discord one-line announcement")
    if lines[0] != lines[0].strip():
        raise ValueError("Changelog.md announcement must not have leading or trailing whitespace")
    return normalized.strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("Changelog.md"))
    parser.add_argument("--output", type=Path, default=Path("dist/CHANGELOG.md"))
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    try:
        rendered = render_changelog(args.source.read_text(encoding="utf-8"), args.version)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"rendered {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
