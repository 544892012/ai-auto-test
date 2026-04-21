from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class CaseDocument:
    """Parsed test case from Markdown + YAML front matter."""

    id: str
    target: str
    device: str
    title: str
    steps: list[str]
    asserts: list[str]
    source_path: Path
    raw_front_matter: dict


def _parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise ValueError("Case file must start with YAML front matter (---)")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("Missing closing --- for front matter")
    fm_raw = text[4:end]
    body = text[end + 5 :]
    data = yaml.safe_load(fm_raw) or {}
    if not isinstance(data, dict):
        raise ValueError("Front matter must be a YAML mapping")
    return data, body


def _section_lines(body: str, heading: str) -> list[str]:
    pattern = rf"^##\s+{re.escape(heading)}\s*$"
    lines = body.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(pattern, line.strip(), re.IGNORECASE):
            start = i + 1
            break
    if start is None:
        raise ValueError(f"Missing section ## {heading}")
    collected: list[str] = []
    for line in lines[start:]:
        if line.startswith("## ") and line.strip().lower() != f"## {heading.lower()}":
            if re.match(r"^##\s+\w", line):
                break
        stripped = line.strip()
        if not stripped:
            continue
        collected.append(stripped)
    return collected


def _normalize_step_line(line: str) -> str | None:
    m = re.match(r"^\d+[\.\)、]\s*(.+)$", line)
    if m:
        return m.group(1).strip()
    if line.startswith(("-", "*", "•")):
        return line.lstrip("-*• ").strip()
    return line


def _normalize_assert_line(line: str) -> str | None:
    if line.startswith(("-", "*", "•")):
        return line.lstrip("-*• ").strip()
    return line


def parse_case_text(text: str, source_path: Path) -> CaseDocument:
    fm, body = _parse_front_matter(text)
    case_id = fm.get("id")
    target = fm.get("target")
    if not case_id or not isinstance(case_id, str):
        raise ValueError("front matter 'id' is required (string)")
    if not target or not isinstance(target, str):
        raise ValueError("front matter 'target' is required (string)")
    device = fm.get("device", "desktop")
    if not isinstance(device, str):
        device = "desktop"

    title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else case_id

    raw_steps = _section_lines(body, "steps")
    raw_asserts = _section_lines(body, "asserts")

    steps: list[str] = []
    for ln in raw_steps:
        norm = _normalize_step_line(ln)
        if norm:
            steps.append(norm)

    asserts: list[str] = []
    for ln in raw_asserts:
        norm = _normalize_assert_line(ln)
        if norm:
            asserts.append(norm)

    return CaseDocument(
        id=case_id,
        target=target,
        device=device,
        title=title,
        steps=steps,
        asserts=asserts,
        source_path=source_path,
        raw_front_matter=fm,
    )


def parse_case_file(path: Path) -> CaseDocument:
    text = path.read_text(encoding="utf-8")
    return parse_case_text(text, path.resolve())
