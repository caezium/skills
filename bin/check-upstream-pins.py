#!/usr/bin/env python3
"""Compare reviewed Git source pins with their current remote branch heads."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


DEFAULT_LOCK = Path(__file__).resolve().parent.parent / "skills.lock.json"


def remote_head(url: str, branch: str) -> str | None:
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", url, f"refs/heads/{branch}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return result.stdout.split()[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    data = json.loads(args.lock.read_text(encoding="utf-8"))
    rows: list[tuple[str, str, str, str]] = []
    attention = False

    for source_id, source in sorted(data["sources"].items()):
        if source["kind"] != "git" or source_id == "personal":
            continue
        pinned = source["pinnedCommit"]
        if not pinned:
            rows.append((source["label"], "unpinned", "-", "review"))
            attention = True
            continue
        current = remote_head(source["url"], source["branch"])
        if current is None:
            rows.append((source["label"], pinned[:12], "unreachable", "review"))
            attention = True
        elif current == pinned:
            rows.append((source["label"], pinned[:12], current[:12], "current"))
        else:
            rows.append((source["label"], pinned[:12], current[:12], "advanced"))
            attention = True

    lines = [
        "# Skill source freshness",
        "",
        "| Source | Reviewed pin | Current head | Status |",
        "|---|---|---|---|",
    ]
    lines.extend(f"| {label} | `{pinned}` | `{current}` | {status} |" for label, pinned, current, status in rows)
    lines.extend(
        [
            "",
            "An advanced or unreachable source requires a reviewed package diff. This check never edits or merges skills.",
            "",
        ]
    )
    report = "\n".join(lines)
    print(report, end="")
    if args.report:
        args.report.write_text(report, encoding="utf-8")
    return 3 if attention else 0


if __name__ == "__main__":
    raise SystemExit(main())
