#!/usr/bin/env python3
"""Archive duplicate skill installs and restore one canonical owner per name."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess


DEFAULT_REPO = Path(__file__).resolve().parent.parent
DISCOVERY_DIRS = (".claude/skills", ".cursor/skills", ".agents/skills")
CODEX_LEGACY_DIR = ".codex/skills"


def exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def canonical_names(repo: Path) -> set[str]:
    return {path.parent.name for path in repo.glob("*/SKILL.md")}


def retired_names(lock: dict) -> set[str]:
    return {
        record["name"]
        for record in lock["skills"]
        if record["state"] == "planned-retire"
    }


def points_to(path: Path, expected: Path) -> bool:
    if not path.is_symlink():
        return False
    raw = Path(os.readlink(path))
    resolved = raw if raw.is_absolute() else path.parent / raw
    return resolved.resolve(strict=False) == expected.resolve(strict=False)


def archive(path: Path, target_home: Path, backup_root: Path, apply: bool) -> bool:
    if not exists(path):
        return False
    relative = path.relative_to(target_home)
    destination = backup_root / relative
    print(f"{'ARCHIVE' if apply else 'WOULD ARCHIVE'} {path} -> {destination}")
    if not apply:
        return True
    if exists(destination):
        raise SystemExit(f"backup destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(destination))
    return True


def prune_external_lock(
    path: Path,
    owned_names: set[str],
    target_home: Path,
    backup_root: Path,
    apply: bool,
) -> int:
    if not path.is_file():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    skills = data.get("skills", {})
    removed = sorted(set(skills).intersection(owned_names))
    if not removed:
        return 0
    print(f"{'PRUNE' if apply else 'WOULD PRUNE'} {len(removed)} canonical/retired entries from {path}")
    for name in removed:
        print(f"  {name}")
    if not apply:
        return len(removed)

    destination = backup_root / path.relative_to(target_home)
    if exists(destination):
        raise SystemExit(f"backup destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
    data["skills"] = {name: value for name, value in skills.items() if name not in owned_names}
    temporary = path.with_name(f"{path.name}.skills-reconcile-tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    return len(removed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument(
        "--target-home",
        type=Path,
        default=Path(os.environ.get("SKILLS_TARGET_HOME", Path.home())),
    )
    parser.add_argument("--backup-label")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    target_home = args.target_home.resolve()
    lock_path = repo / "skills.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    active = canonical_names(repo)
    retired = retired_names(lock)
    owned = active | retired
    label = args.backup_label or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = target_home / ".skill-backups" / f"discovery-{label}"
    archived = 0

    for name in sorted(active):
        expected = repo / name
        for relative in DISCOVERY_DIRS:
            target = target_home / relative / name
            if exists(target) and not points_to(target, expected):
                archived += int(archive(target, target_home, backup_root, args.apply))
        legacy_codex = target_home / CODEX_LEGACY_DIR / name
        archived += int(archive(legacy_codex, target_home, backup_root, args.apply))

    for name in sorted(retired):
        for relative in (*DISCOVERY_DIRS, CODEX_LEGACY_DIR):
            archived += int(archive(target_home / relative / name, target_home, backup_root, args.apply))

    pruned = prune_external_lock(
        target_home / ".agents" / ".skill-lock.json",
        owned,
        target_home,
        backup_root,
        args.apply,
    )

    if not args.apply:
        print(f"RESULT dry run: {archived} path(s), {pruned} lock record(s) need reconciliation")
        print("Run again with --apply to archive them and restore canonical links.")
        return 3 if archived or pruned else 0

    subprocess.run(
        [str(repo / "bin" / "sync.sh"), "all"],
        check=True,
        env={**os.environ, "SKILLS_REPO": str(repo), "SKILLS_TARGET_HOME": str(target_home)},
    )
    if archived or pruned:
        print(f"BACKUP {backup_root}")
    print(f"RESULT reconciled {archived} path(s) and {pruned} external lock record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
