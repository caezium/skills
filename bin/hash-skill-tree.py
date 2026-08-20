#!/usr/bin/env python3
"""Return a portable SHA-256 for one skill directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


IGNORED_DIRS = {".git", ".pytest_cache", "__pycache__"}
IGNORED_FILES = {".DS_Store"}


def digest_tree(root: Path) -> str:
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    digest = hashlib.sha256()
    paths: list[Path] = []
    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirnames[:] = sorted(name for name in dirnames if name not in IGNORED_DIRS)
        base = Path(current)
        for name in sorted(filenames):
            if name in IGNORED_FILES or name.endswith(".pyc"):
                continue
            paths.append(base / name)
        for name in dirnames:
            candidate = base / name
            if candidate.is_symlink():
                paths.append(candidate)

    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        if path.is_symlink():
            digest.update(b"L\0" + relative + b"\0")
            digest.update(os.readlink(path).encode("utf-8") + b"\0")
            continue
        executable = b"1" if path.stat().st_mode & 0o111 else b"0"
        payload = path.read_bytes()
        digest.update(b"F\0" + relative + b"\0" + executable + b"\0")
        digest.update(str(len(payload)).encode("ascii") + b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path, nargs="?")
    parser.add_argument("--verify-lock", type=Path)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    if args.verify_lock:
        if args.directory is not None or args.root is None:
            parser.error("--verify-lock requires --root and no directory argument")
        try:
            lock = json.loads(args.verify_lock.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            parser.error(str(exc))
        mismatches = 0
        checked = 0
        for skill in lock.get("skills", []):
            if skill.get("state") == "planned-retire":
                continue
            path = args.root / skill["name"]
            if not (path / "SKILL.md").is_file():
                continue
            content = skill.get("content", {})
            if content.get("kind") != "sha256":
                continue
            actual = digest_tree(path.resolve())
            expected = content.get("value")
            checked += 1
            if actual != expected:
                mismatches += 1
                print(f"DRIFT {skill['name']}: expected {expected}, found {actual}")
        if mismatches:
            print(f"DRIFT {mismatches} of {checked} checked skill trees differ")
            return 3
        print(f"OK    {checked} skill tree content pins match")
        return 0
    if args.directory is None or args.root is not None:
        parser.error("provide one directory, or use --verify-lock with --root")
    try:
        print(digest_tree(args.directory.resolve()))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
