#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

try:
    from central_memory_backend_client import load_backend_env_if_present
except ImportError:  # pragma: no cover - fallback when hook bundle is incomplete
    def load_backend_env_if_present() -> dict[str, str]:
        return {}


load_backend_env_if_present()

CANONICAL_BUCKETS = {
    "org",
    "products",
    "domains",
    "repos",
    "specs",
    "adr",
    "incidents",
    "runbooks",
    "glossary",
    "integrations",
}

PROPOSAL_STATUSES = {"draft", "ready", "promoted", "rejected", "approved"}
PROMOTION_RECORD_HEADINGS = {
    "Promotion decision",
    "Checklist",
    "Acceptance criteria",
    "Promoted notes",
    "Rejected notes",
    "Deprecated notes",
    "Conflicts to resolve",
    "Next sync",
}
PROPOSAL_HEADINGS = {
    "Problem",
    "Proposal",
    "Consequences",
    "Sources",
    "Acceptance criteria",
}


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"null", "~"}:
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not match:
        return {}, text

    raw_frontmatter, body = match.groups()
    data: dict[str, Any] = {}
    current_key: str | None = None
    list_mode = False

    for raw_line in raw_frontmatter.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue

        key_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if key_match:
            key = key_match.group(1)
            value = key_match.group(2)
            current_key = key
            if value == "":
                data[key] = []
                list_mode = True
            else:
                data[key] = parse_scalar(value)
                list_mode = False
            continue

        list_match = re.match(r"^\s*-\s*(.*)$", line)
        if list_mode and current_key and list_match:
            data[current_key].append(parse_scalar(list_match.group(1)))

    return data, body


def format_frontmatter(data: dict[str, Any]) -> str:
    preferred_order = [
        "id",
        "type",
        "scope",
        "status",
        "owner",
        "source",
        "target_path",
        "supersedes",
        "confidence",
        "reviewed_at",
        "promoted_to",
        "promoted_at",
    ]
    keys = [key for key in preferred_order if key in data]
    keys.extend(key for key in data.keys() if key not in keys)

    lines = ["---"]
    for key in keys:
        value = data[key]
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def load_markdown(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    return parse_frontmatter(text)


def write_markdown(path: Path, meta: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    output = f"{format_frontmatter(meta)}\n\n{body.rstrip()}\n"
    path.write_text(output, encoding="utf-8")


def sections(body: str) -> dict[str, str]:
    result: dict[str, list[str]] = {}
    current: str | None = None
    lines: list[str] = []

    for line in body.splitlines():
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            if current is not None:
                result[current] = lines.copy()
            current = heading.group(2).strip()
            lines = []
            continue

        if current is not None:
            lines.append(line)

    if current is not None:
        result[current] = lines

    return {key: "\n".join(value).strip() for key, value in result.items()}


def bullet_lines(text: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r"^\s*-\s+(.*)$", text, re.M)
    ]


def checkbox_lines(text: str) -> list[tuple[bool, str]]:
    matches: list[tuple[bool, str]] = []
    for match in re.finditer(r"^\s*-\s+\[([ xX])\]\s+(.*)$", text, re.M):
        matches.append((match.group(1).lower() == "x", match.group(2).strip()))
    return matches


def is_canonical_path(path: Path) -> bool:
    parts = path.parts
    if "_proposals" in parts:
        return False
    if "knowledge" not in parts:
        return False
    try:
        knowledge_index = parts.index("knowledge")
    except ValueError:
        return False
    if knowledge_index + 1 >= len(parts):
        return False
    return parts[knowledge_index + 1] in CANONICAL_BUCKETS


def normalize_note(meta: dict[str, Any], body: str) -> str:
    body = body.rstrip()
    return f"{format_frontmatter(meta)}\n\n{body}\n"


def stable_meta(meta: dict[str, Any]) -> dict[str, Any]:
    stable = dict(meta)
    for key in ("target_path", "reviewed_at", "promoted_to", "promoted_at"):
        stable.pop(key, None)
    return stable


def validate_proposal(path: Path) -> list[str]:
    errors: list[str] = []
    meta, body = load_markdown(path)
    body_sections = sections(body)

    required_keys = ["id", "type", "scope", "status", "owner", "target_path", "supersedes", "confidence"]
    for key in required_keys:
        if key not in meta:
            errors.append(f"{path}: missing frontmatter field `{key}`")

    if meta.get("type") != "proposal":
        errors.append(f"{path}: `type` must be `proposal`")

    status = str(meta.get("status", "")).lower()
    if status and status not in PROPOSAL_STATUSES:
        errors.append(f"{path}: unsupported proposal status `{meta.get('status')}`")

    target_path = meta.get("target_path")
    if not isinstance(target_path, str) or not target_path.startswith("knowledge/"):
        errors.append(f"{path}: `target_path` must point inside `knowledge/`")
    elif "_proposals" in Path(target_path).parts:
        errors.append(f"{path}: `target_path` must not point back into `_proposals`")

    for heading in PROPOSAL_HEADINGS:
        if heading not in body_sections:
            errors.append(f"{path}: missing `## {heading}` section")

    source = meta.get("source")
    source_from_frontmatter = isinstance(source, list) and bool(source)
    source_from_body = bool(bullet_lines(body_sections.get("Sources", "")))
    if not source_from_frontmatter and not source_from_body:
        errors.append(
            f"{path}: proposal needs a non-empty source trail in frontmatter `source` or `## Sources`"
        )

    if "Sources" in body_sections:
        sources = bullet_lines(body_sections["Sources"])
        if not sources:
            errors.append(f"{path}: `Sources` must contain at least one bullet")

    if "Acceptance criteria" in body_sections:
        acceptance = bullet_lines(body_sections["Acceptance criteria"])
        if not acceptance:
            errors.append(f"{path}: `Acceptance criteria` must contain at least one bullet")
    else:
        errors.append(f"{path}: missing `## Acceptance criteria` section")

    checklist = body_sections.get("Checklist")
    if checklist:
        checkboxes = checkbox_lines(checklist)
        if checkboxes and not all(item[0] for item in checkboxes):
            errors.append(f"{path}: checklist contains unchecked items")

    return errors


def validate_promotion_record(path: Path) -> list[str]:
    errors: list[str] = []
    meta, body = load_markdown(path)
    body_sections = sections(body)

    required_keys = ["id", "type", "scope", "status", "owner", "source", "supersedes"]
    for key in required_keys:
        if key not in meta:
            errors.append(f"{path}: missing frontmatter field `{key}`")

    if meta.get("type") != "canonical":
        errors.append(f"{path}: `type` must be `canonical`")

    for heading in PROMOTION_RECORD_HEADINGS:
        if heading not in body_sections:
            errors.append(f"{path}: missing `## {heading}` section")

    for heading in ("Checklist", "Acceptance criteria"):
        section = body_sections.get(heading)
        if not section:
            continue
        checkboxes = checkbox_lines(section)
        if not checkboxes:
            errors.append(f"{path}: `{heading}` must contain checkbox items")
        elif not all(item[0] for item in checkboxes):
            errors.append(f"{path}: `{heading}` contains unchecked items")

    promoted_notes = body_sections.get("Promoted notes", "")
    if promoted_notes.strip() == "None":
        errors.append(f"{path}: `Promoted notes` must list at least one promoted path")
    elif not bullet_lines(promoted_notes):
        errors.append(f"{path}: `Promoted notes` must contain at least one bullet")

    return errors


def validate_any(path: Path) -> list[str]:
    meta, body = load_markdown(path)
    body_sections = sections(body)
    if "Promotion decision" in body_sections or "Checklist" in body_sections:
        return validate_promotion_record(path)
    if meta.get("type") == "proposal" or "Proposal" in body_sections:
        return validate_proposal(path)
    return [f"{path}: unable to determine artifact type for validation"]


def guard_write(path: Path) -> list[str]:
    if is_canonical_path(path):
        return [
            f"blocked direct write to canonical path: {path}",
            "use a proposal in `knowledge/_proposals/` and promote it with `hooks/memory_hooks.py promote-ready`",
        ]
    return []


def promote_ready(queue_root: Path, dry_run: bool = False) -> tuple[list[str], bool]:
    messages: list[str] = []
    had_error = False
    if not queue_root.exists():
        return [f"{queue_root}: queue directory does not exist"], True

    for proposal_path in sorted(queue_root.rglob("*.md")):
        if proposal_path.name == "README.md":
            continue

        meta, body = load_markdown(proposal_path)
        if meta.get("type") != "proposal":
            continue
        if str(meta.get("status", "")).lower() not in {"ready", "approved"}:
            continue

        errors = validate_proposal(proposal_path)
        if errors:
            messages.extend(errors)
            had_error = True
            continue

        target_raw = meta["target_path"]
        assert isinstance(target_raw, str)
        target_path = Path(target_raw)

        canonical_meta = dict(meta)
        canonical_meta.pop("target_path", None)
        canonical_meta["type"] = "canonical"
        canonical_meta["status"] = "active"
        canonical_meta["reviewed_at"] = date.today().isoformat()

        if target_path.exists():
            existing_text = target_path.read_text(encoding="utf-8")
            existing_meta, existing_body = parse_frontmatter(existing_text)
            if normalize_note(stable_meta(existing_meta), existing_body) != normalize_note(
                stable_meta(canonical_meta), body
            ):
                messages.append(
                    f"{proposal_path}: target `{target_path}` already exists with different content"
                )
                had_error = True
                continue

        if dry_run:
            messages.append(f"[dry-run] would promote {proposal_path} -> {target_path}")
        else:
            write_markdown(target_path, canonical_meta, body)
            promoted_meta = dict(meta)
            promoted_meta["status"] = "promoted"
            promoted_meta["promoted_to"] = str(target_path)
            promoted_meta["promoted_at"] = date.today().isoformat()
            write_markdown(proposal_path, promoted_meta, body)
            messages.append(f"promoted {proposal_path} -> {target_path}")

    if not messages:
        messages.append(f"{queue_root}: no ready proposals found")
    return messages, had_error


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and promote memory artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a markdown artifact.")
    validate_parser.add_argument("path", type=Path)

    validate_proposal_parser = subparsers.add_parser(
        "validate-proposal", help="Validate a proposal draft."
    )
    validate_proposal_parser.add_argument("path", type=Path)

    validate_promotion_parser = subparsers.add_parser(
        "validate-promotion", help="Validate a promotion record or proposal artifact."
    )
    validate_promotion_parser.add_argument("path", type=Path)

    guard_parser = subparsers.add_parser(
        "guard-write", help="Block unsafe writes to canonical knowledge."
    )
    guard_parser.add_argument("--path", required=True, type=Path)
    guard_parser.add_argument("--tool", default="Write")

    promote_parser = subparsers.add_parser(
        "promote-ready", help="Promote ready proposals from the queue."
    )
    promote_parser.add_argument(
        "--queue", default=Path("knowledge/_proposals"), type=Path
    )
    promote_parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.command == "validate":
        errors = validate_any(args.path)
    elif args.command == "validate-proposal":
        errors = validate_proposal(args.path)
    elif args.command == "validate-promotion":
        errors = validate_any(args.path)
    elif args.command == "guard-write":
        errors = guard_write(args.path)
        if errors:
            eprint("\n".join(errors))
            return 1
        print(f"allowed write to {args.path}")
        return 0
    elif args.command == "promote-ready":
        messages, had_error = promote_ready(args.queue, dry_run=args.dry_run)
        print("\n".join(messages))
        return 1 if had_error else 0
    else:
        errors = [f"unknown command: {args.command}"]

    if errors:
        eprint("\n".join(errors))
        return 1

    print(f"{args.command}: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
