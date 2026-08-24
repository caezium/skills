#!/usr/bin/env python3
"""Validate portable structure and metadata for every canonical skill."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import unquote


DEFAULT_ROOT = Path(__file__).resolve().parent.parent
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def frontmatter(text: str) -> tuple[dict[str, str], str | None]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "missing opening frontmatter delimiter"
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}, "missing closing frontmatter delimiter"

    values: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if match:
            value = match.group(2)
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            values[match.group(1)] = value
    return values, None


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    metadata, metadata_error = frontmatter(text)

    if metadata_error:
        errors.append(metadata_error)
        return errors

    name = metadata.get("name", "")
    if name != skill_dir.name:
        errors.append(f"frontmatter name {name!r} does not match directory {skill_dir.name!r}")
    if not NAME_RE.fullmatch(name) or len(name) > 64:
        errors.append("name must be lowercase hyphen-case and at most 64 characters")
    if not metadata.get("description"):
        errors.append("frontmatter description is missing or empty")

    for nested_git in skill_dir.rglob(".git"):
        errors.append(f"embedded Git metadata is not allowed: {nested_git.relative_to(skill_dir)}")

    for raw_target in MARKDOWN_LINK_RE.findall(text):
        target = raw_target.strip().split()[0].strip("<>")
        if not target or target.startswith(("#", "http://", "https://", "mailto:", "skill://")):
            continue
        relative = unquote(target.split("#", 1)[0])
        if not relative.startswith(("assets/", "references/", "scripts/")):
            continue
        if not (skill_dir / relative).exists():
            errors.append(f"referenced package file is missing: {relative}")

    openai = skill_dir / "agents" / "openai.yaml"
    if openai.exists():
        yaml_text = openai.read_text(encoding="utf-8")
        if not re.search(r"^interface:\s*$", yaml_text, re.MULTILINE):
            errors.append("agents/openai.yaml is missing interface metadata")
        if not re.search(r"^\s+display_name:\s*\S", yaml_text, re.MULTILINE):
            errors.append("agents/openai.yaml is missing interface.display_name")
        if not re.search(r"^\s+short_description:\s*\S", yaml_text, re.MULTILINE):
            errors.append("agents/openai.yaml is missing interface.short_description")
        for value in re.findall(r"allow_implicit_invocation:\s*(\S+)", yaml_text):
            if value not in {"true", "false"}:
                errors.append("allow_implicit_invocation must be true or false")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    skill_dirs = sorted(path.parent for path in root.glob("*/SKILL.md"))
    failures = 0

    for skill_dir in skill_dirs:
        for error in validate_skill(skill_dir):
            failures += 1
            print(f"ERROR {skill_dir.name}: {error}")

    if failures:
        print(f"RESULT {failures} skill-tree error(s) across {len(skill_dirs)} skills")
        return 2
    print(f"RESULT {len(skill_dirs)} skill packages are structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
