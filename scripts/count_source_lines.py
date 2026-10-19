#!/usr/bin/env python3
"""Inventory likely first-party source files without counting generated/vendor artifacts.

This is a transparent estimate, not a RustLabs certification. Review the output and the
reviewer's inclusion rules before relying on it for any external submission.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SUFFIXES = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript/JSX",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript/JSX",
    ".java": "Java",
    ".kt": "Kotlin",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".cc": "C++",
    ".c": "C",
    ".h": "C/C++ header",
    ".hpp": "C++ header",
    ".swift": "Swift",
    ".sql": "SQL",
}
EXCLUDED_PARTS = {
    ".git", ".venv", "venv", "node_modules", "dist", "build", "target",
    "coverage", ".pytest_cache", "__pycache__", "vendor", "third_party",
}
EXCLUDED_NAMES = {
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock",
    "Pipfile.lock", "Cargo.lock", "composer.lock", "Gemfile.lock",
}
GENERATED_MARKERS = ("generated", "do not edit", "automatically generated")


def inventory() -> tuple[dict[str, dict[str, int]], list[tuple[str, int, int]]]:
    totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {"files": 0, "physical_lines": 0, "nonblank_lines": 0}
    )
    files: list[tuple[str, int, int]] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.name in EXCLUDED_NAMES or "migrations" in relative.parts:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        first_lines = "\n".join(content.splitlines()[:3]).lower()
        if any(marker in first_lines for marker in GENERATED_MARKERS):
            continue
        lines = content.splitlines()
        nonblank = sum(bool(line.strip()) for line in lines)
        language = SOURCE_SUFFIXES[path.suffix.lower()]
        totals[language]["files"] += 1
        totals[language]["physical_lines"] += len(lines)
        totals[language]["nonblank_lines"] += nonblank
        files.append((relative.as_posix(), len(lines), nonblank))
    return dict(totals), files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=20, help="show the largest source files")
    args = parser.parse_args()
    totals, files = inventory()
    print("First-party source inventory (migrations/build/vendor/generated files excluded)")
    print("Language                 Files   Physical lines   Nonblank lines")
    for language, values in sorted(totals.items()):
        print(
            f"{language:24} {values['files']:>5} "
            f"{values['physical_lines']:>15} {values['nonblank_lines']:>16}"
        )
    physical = sum(item["physical_lines"] for item in totals.values())
    nonblank = sum(item["nonblank_lines"] for item in totals.values())
    print(f"TOTAL                    {len(files):>5} {physical:>15} {nonblank:>16}")
    print("\nLargest files by physical lines:")
    for name, lines, nonblank_lines in sorted(files, key=lambda item: item[1], reverse=True)[:args.top]:
        print(f"{lines:>6} lines ({nonblank_lines:>6} nonblank)  {name}")
    print("\nNote: nonblank lines include comments and whitespace-only semantics are not interpreted.")
    print("This is an estimate; a reviewer may apply different inclusion/exclusion rules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
