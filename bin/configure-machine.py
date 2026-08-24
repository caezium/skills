#!/usr/bin/env python3
"""Install the shared Claude guardrail and deterministic session-start sync."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil


DEFAULT_REPO = Path(__file__).resolve().parent.parent
SYNC_ALL = "~/skills/bin/sync.sh all"
SYNC_CLAUDE = "~/skills/bin/sync.sh claude"
GUARDRAIL_COMMAND = "~/.claude/hooks/block-dangerous-git.sh"


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
    settings_path = target_home / ".claude" / "settings.json"
    hook_path = target_home / ".claude" / "hooks" / "block-dangerous-git.sh"
    source_hook = repo / "git-guardrails-claude-code" / "scripts" / "block-dangerous-git.sh"
    if not source_hook.is_file():
        raise SystemExit(f"missing guardrail source: {source_hook}")

    data = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit(f"hooks must be an object in {settings_path}")

    session_start = hooks.setdefault("SessionStart", [])
    if not isinstance(session_start, list):
        raise SystemExit(f"hooks.SessionStart must be an array in {settings_path}")
    has_sync_all = False
    for entry in session_start:
        for hook in entry.get("hooks", []):
            if hook.get("command") == SYNC_CLAUDE:
                hook["command"] = SYNC_ALL
            if hook.get("command") == SYNC_ALL:
                has_sync_all = True
    if not has_sync_all:
        session_start.insert(0, {"hooks": [{"type": "command", "command": SYNC_ALL}]})

    pre_tool = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool, list):
        raise SystemExit(f"hooks.PreToolUse must be an array in {settings_path}")
    if not any(
        hook.get("command") == GUARDRAIL_COMMAND
        for entry in pre_tool
        for hook in entry.get("hooks", [])
    ):
        pre_tool.append(
            {
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": GUARDRAIL_COMMAND}],
            }
        )

    if not args.apply:
        print(f"WOULD WRITE {settings_path}")
        print(f"WOULD INSTALL {hook_path}")
        print("Run again with --apply to configure this machine.")
        return 3

    label = args.backup_label or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = target_home / ".skill-backups" / f"machine-config-{label}"
    if settings_path.exists():
        destination = backup_root / ".claude" / "settings.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(settings_path, destination)
    if hook_path.exists():
        destination = backup_root / ".claude" / "hooks" / hook_path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(hook_path, destination)

    hook_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_hook, hook_path)
    hook_path.chmod(hook_path.stat().st_mode | 0o111)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = settings_path.with_name(f"{settings_path.name}.skills-config-tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, settings_path)
    print(f"BACKUP {backup_root}")
    print(f"RESULT configured {settings_path} and {hook_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
