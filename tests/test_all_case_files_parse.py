from __future__ import annotations

from pathlib import Path

import pytest

from aitest.case_parser import parse_case_file


def _case_files() -> list[Path]:
    root = Path(__file__).resolve().parents[1]
    return sorted((root / "cases").glob("*.md"))


@pytest.mark.parametrize("path", _case_files(), ids=lambda p: p.stem)
def test_case_file_parses(path: Path) -> None:
    doc = parse_case_file(path)
    assert doc.id
    assert doc.target.startswith("http")
    assert len(doc.steps) >= 1
    assert len(doc.asserts) >= 1
