#!/usr/bin/env python3
"""Dependency-free JSON Schema subset plus lock-specific semantic checks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def load_object(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: cannot parse {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label}: top level must be an object")
        return {}
    return value


def type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def resolve_ref(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"only local JSON pointers are supported: {reference}")
    value: Any = root_schema
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        value = value[part]
    if not isinstance(value, dict):
        raise ValueError(f"schema reference does not resolve to an object: {reference}")
    return value


def valid_datetime(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def validate_instance(
    value: Any,
    rule: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    if "$ref" in rule:
        try:
            target = resolve_ref(root_schema, rule["$ref"])
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"schema {path}: {exc}")
            return
        validate_instance(value, target, root_schema, path, errors)
        return

    if "anyOf" in rule:
        branches = rule["anyOf"]
        if not isinstance(branches, list) or not branches:
            errors.append(f"schema {path}: anyOf must be a non-empty array")
            return
        for branch in branches:
            branch_errors: list[str] = []
            validate_instance(value, branch, root_schema, path, branch_errors)
            if not branch_errors:
                return
        errors.append(f"{path}: value does not match any allowed schema")
        return

    if "const" in rule and value != rule["const"]:
        errors.append(f"{path}: must equal {rule['const']!r}")
    if "enum" in rule and value not in rule["enum"]:
        errors.append(f"{path}: {value!r} is not one of {rule['enum']!r}")

    expected_type = rule.get("type")
    if expected_type is not None:
        expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(type_matches(value, item) for item in expected_types):
            errors.append(f"{path}: expected type {expected_types!r}, found {type(value).__name__}")
            return

    if isinstance(value, dict):
        required = rule.get("required", [])
        if not isinstance(required, list):
            errors.append(f"schema {path}: required must be an array")
            required = []
        for name in required:
            if name not in value:
                errors.append(f"{path}.{name}: required property is missing")
        properties = rule.get("properties", {})
        if not isinstance(properties, dict):
            errors.append(f"schema {path}: properties must be an object")
            properties = {}
        for name, child in value.items():
            child_path = f"{path}.{name}"
            if name in properties:
                validate_instance(child, properties[name], root_schema, child_path, errors)
                continue
            additional = rule.get("additionalProperties", True)
            if additional is False:
                errors.append(f"{child_path}: additional property is not allowed")
            elif isinstance(additional, dict):
                validate_instance(child, additional, root_schema, child_path, errors)

    if isinstance(value, list):
        minimum = rule.get("minItems")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{path}: needs at least {minimum} item(s)")
        if rule.get("uniqueItems") is True:
            encoded = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value]
            if len(encoded) != len(set(encoded)):
                errors.append(f"{path}: items must be unique")
        item_rule = rule.get("items")
        if isinstance(item_rule, dict):
            for index, child in enumerate(value):
                validate_instance(child, item_rule, root_schema, f"{path}[{index}]", errors)

    if isinstance(value, str):
        minimum = rule.get("minLength")
        maximum = rule.get("maxLength")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{path}: shorter than minLength {minimum}")
        if isinstance(maximum, int) and len(value) > maximum:
            errors.append(f"{path}: longer than maxLength {maximum}")
        pattern = rule.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            errors.append(f"{path}: does not match pattern {pattern!r}")
        if rule.get("format") == "date-time" and not valid_datetime(value):
            errors.append(f"{path}: must be an ISO-8601 date-time with timezone")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lockfile", type=Path)
    parser.add_argument("--schema", type=Path, required=True)
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    schema = load_object(args.schema, "schema", errors)
    lock = load_object(args.lockfile, "lockfile", errors)
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 2

    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("schema must identify JSON Schema draft 2020-12")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        errors.append("schema top level must be a closed object")
    for definition in ("source", "contentPin", "skill"):
        if not isinstance(schema.get("$defs", {}).get(definition), dict):
            errors.append(f"schema $defs.{definition} is required")

    validate_instance(lock, schema, schema, "$", errors)

    sources = lock.get("sources", {}) if isinstance(lock.get("sources"), dict) else {}
    for source_id, source in sources.items():
        if not isinstance(source, dict):
            continue
        if source.get("kind") == "git":
            if not source.get("repo") or not source.get("url") or not source.get("branch"):
                errors.append(f"sources.{source_id}: git sources require repo, url, and branch")
            if source.get("pinnedCommit") is None:
                warnings.append(f"git source {source_id} has no pinned commit")
        elif source.get("kind") in {"managed", "unknown"}:
            for field in ("url", "branch", "pinnedCommit"):
                if source.get(field) is not None:
                    errors.append(f"sources.{source_id}.{field}: must be null for {source.get('kind')} source")

    skills = lock.get("skills", []) if isinstance(lock.get("skills"), list) else []
    records: dict[str, dict[str, Any]] = {}
    names: list[str] = []
    for index, skill in enumerate(skills):
        if not isinstance(skill, dict) or not isinstance(skill.get("name"), str):
            continue
        name = skill["name"]
        if name in records:
            errors.append(f"skills[{index}].name: duplicate skill name {name!r}")
        names.append(name)
        records[name] = skill
        source_id = skill.get("sourceId")
        if source_id is not None and source_id not in sources:
            errors.append(f"{name}: unknown sourceId {source_id!r}")
        if skill.get("kind") in {"vendored", "vendored-overlay", "managed-mirror"} and source_id is None:
            errors.append(f"{name}: {skill.get('kind')} entries require a sourceId")
        if skill.get("kind") == "source-unknown" and source_id is not None:
            errors.append(f"{name}: source-unknown must not claim a sourceId")
        overlays = skill.get("localOverlays")
        if isinstance(overlays, list):
            if overlays and skill.get("kind") != "vendored-overlay":
                errors.append(f"{name}: localOverlays require kind vendored-overlay")
            if skill.get("kind") == "vendored-overlay" and not overlays:
                errors.append(f"{name}: vendored-overlay must describe at least one overlay")

    if names != sorted(names):
        errors.append("skills must be sorted by name")
    for name, skill in records.items():
        replacements = skill.get("replacedBy", [])
        if not isinstance(replacements, list):
            continue
        for replacement in replacements:
            if not isinstance(replacement, str):
                continue
            if replacement not in records:
                errors.append(f"{name}: replacedBy target {replacement!r} is missing")
            elif records[replacement].get("state") == "planned-retire":
                errors.append(f"{name}: replacedBy target {replacement!r} is also retiring")

    counts = {state: 0 for state in ("active", "planned-add", "planned-retire")}
    for skill in skills:
        if isinstance(skill, dict) and skill.get("state") in counts:
            counts[skill["state"]] += 1

    for warning in warnings:
        print(f"WARN  {warning}")
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 2
    print(
        "OK    lockfile valid: "
        f"{len(skills)} records "
        f"({counts['active']} active, {counts['planned-add']} planned-add, "
        f"{counts['planned-retire']} planned-retire), {len(sources)} sources"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
