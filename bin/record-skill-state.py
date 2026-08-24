#!/usr/bin/env python3
"""Update one provenance record without hand-editing skills.lock.json."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_REPO = SCRIPT_DIR.parent


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_hasher():
    path = SCRIPT_DIR / "hash-skill-tree.py"
    spec = importlib.util.spec_from_file_location("hash_skill_tree", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_value(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def read_lock(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_lock(path: Path, data: dict, checked_at: str) -> None:
    data["generatedAt"] = checked_at
    data["skills"] = sorted(data["skills"], key=lambda item: item["name"])
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def find_record(data: dict, name: str) -> dict | None:
    return next((item for item in data["skills"] if item["name"] == name), None)


def command_record(args: argparse.Namespace, data: dict, checked_at: str) -> None:
    repo = args.repo.resolve()
    path = repo / args.name
    if not (path / "SKILL.md").is_file():
        raise SystemExit(f"missing canonical skill: {path}/SKILL.md")

    hasher = load_hasher()
    digest = hasher.digest_tree(path)
    source_tree = None
    if args.source_root:
        source_tree = git_value(args.source_root.resolve(), "rev-parse", f"HEAD:{args.source_path}")

    record = find_record(data, args.name)
    if record is None:
        record = {"name": args.name}
        data["skills"].append(record)

    record.update(
        {
            "state": "active",
            "kind": args.kind,
            "sourceId": args.source_id,
            "sourcePath": args.source_path,
            "sourceTree": source_tree,
            "content": {
                "kind": "sha256",
                "value": digest,
                "basis": "integration-target-content",
            },
            "localOverlays": args.overlay,
            "updatePolicy": args.update_policy,
            "lastCheckedAt": checked_at,
            "notes": args.notes,
        }
    )
    record.pop("replacedBy", None)


def command_retire(args: argparse.Namespace, data: dict, checked_at: str) -> None:
    record = find_record(data, args.name)
    if record is None:
        raise SystemExit(f"no lock record for {args.name}")
    record["state"] = "planned-retire"
    record["kind"] = "legacy-vendored"
    record["sourcePath"] = None
    record["sourceTree"] = None
    record["content"]["basis"] = "canonical-at-pinned-commit"
    record["updatePolicy"] = "frozen-pending-decision"
    record["lastCheckedAt"] = checked_at
    record["notes"] = args.notes
    record["replacedBy"] = args.replaced_by


def command_pin_source(args: argparse.Namespace, data: dict, checked_at: str) -> None:
    source = data["sources"].get(args.source_id)
    if source is None:
        source = {
            "kind": "git",
            "label": args.label,
            "repo": args.remote_repo,
            "url": args.url,
            "branch": args.branch,
            "pinnedCommit": None,
            "pinBasis": "audited-remote-snapshot",
            "lastCheckedAt": checked_at,
        }
        data["sources"][args.source_id] = source
    source["pinnedCommit"] = git_value(args.source_root.resolve(), "rev-parse", "HEAD")
    source["lastCheckedAt"] = checked_at


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--lock", type=Path)
    parser.add_argument("--checked-at", help="ISO-8601 timestamp; defaults to now")
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record")
    record.add_argument("--name", required=True)
    record.add_argument("--source-id")
    record.add_argument("--source-path")
    record.add_argument("--source-root", type=Path)
    record.add_argument("--kind", required=True)
    record.add_argument("--update-policy", required=True)
    record.add_argument("--overlay", action="append", default=[])
    record.add_argument("--notes", default="")

    retire = sub.add_parser("retire")
    retire.add_argument("--name", required=True)
    retire.add_argument("--replaced-by", action="append", default=[])
    retire.add_argument("--notes", required=True)

    source = sub.add_parser("pin-source")
    source.add_argument("--source-id", required=True)
    source.add_argument("--source-root", type=Path, required=True)
    source.add_argument("--label", required=True)
    source.add_argument("--remote-repo", required=True)
    source.add_argument("--url", required=True)
    source.add_argument("--branch", default="main")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    repo = args.repo.resolve()
    lock = (args.lock or repo / "skills.lock.json").resolve()
    checked_at = args.checked_at or now()
    data = read_lock(lock)

    if args.command == "record":
        if bool(args.source_root) != bool(args.source_path):
            parser.error("record requires both --source-root and --source-path, or neither")
        command_record(args, data, checked_at)
    elif args.command == "retire":
        command_retire(args, data, checked_at)
    else:
        command_pin_source(args, data, checked_at)

    write_lock(lock, data, checked_at)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() if exc.stderr else str(exc)
        print(detail, file=sys.stderr)
        raise SystemExit(exc.returncode)
