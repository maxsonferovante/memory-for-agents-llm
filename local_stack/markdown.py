from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


WORD_RE = re.compile(r"[A-Za-z0-9_À-ÿ]+", re.UNICODE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.S)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class MarkdownSection:
    heading_path: str
    content: str


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    raw_frontmatter, body = match.groups()
    result: dict[str, object] = {}
    current_key: str | None = None
    list_mode = False

    for raw_line in raw_frontmatter.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        key_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if key_match:
            current_key = key_match.group(1)
            value = key_match.group(2)
            if value == "":
                result[current_key] = []
                list_mode = True
            elif value.lower() in {"true", "false"}:
                result[current_key] = value.lower() == "true"
                list_mode = False
            else:
                result[current_key] = value
                list_mode = False
            continue

        list_match = re.match(r"^\s*-\s*(.*)$", line)
        if list_mode and current_key and list_match:
            items = result.setdefault(current_key, [])
            if isinstance(items, list):
                items.append(list_match.group(1).strip())

    return result, body


def render_excerpt(text: str, limit: int = 280) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def first_sentence(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return ""
    parts = SENTENCE_RE.split(cleaned, maxsplit=1)
    return parts[0].strip()


def derive_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        heading = HEADING_RE.match(line)
        if heading and heading.group(1) == "#":
            return heading.group(2).strip()
    return fallback


def derive_sections(text: str) -> list[MarkdownSection]:
    sections: list[MarkdownSection] = []
    current_heading: list[str] = []
    current_lines: list[str] = []

    def flush() -> None:
        if current_lines:
            sections.append(
                MarkdownSection(
                    heading_path=" > ".join(current_heading) if current_heading else "document",
                    content="\n".join(current_lines).strip(),
                )
            )

    for line in text.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            flush()
            level = len(heading.group(1))
            current_heading[:] = current_heading[: level - 1]
            current_heading.append(heading.group(2).strip())
            current_lines = []
            continue
        current_lines.append(line)

    flush()
    if not sections and text.strip():
        sections.append(MarkdownSection("document", text.strip()))
    return sections


def chunk_text(text: str, max_chars: int = 900) -> list[str]:
    normalized = re.sub(r"\n{3,}", "\n\n", text.strip())
    if not normalized:
        return []

    paragraphs = [part.strip() for part in normalized.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        if len(paragraph) <= max_chars:
            current = paragraph
            continue
        start = 0
        while start < len(paragraph):
            chunks.append(paragraph[start : start + max_chars])
            start += max_chars

    if current:
        chunks.append(current)

    return chunks


def estimate_tokens(text: str) -> int:
    return len(WORD_RE.findall(text))


def hash_embedding(text: str, dimensions: int = 48) -> list[float]:
    vector = [0.0] * dimensions
    for word in WORD_RE.findall(text.lower()):
        digest = hashlib.sha256(word.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = -1.0 if digest[4] & 1 else 1.0
        weight = 1.0 + (digest[5] / 255.0)
        vector[index] += sign * weight
    norm = math.sqrt(sum(value * value for value in vector))
    if norm:
        vector = [value / norm for value in vector]
    return vector


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    return sum(left[index] * right[index] for index in range(size))


def load_json_file(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))

