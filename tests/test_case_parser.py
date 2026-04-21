from __future__ import annotations

from pathlib import Path

from aitest.case_parser import parse_case_file


def test_parse_example_baidu() -> None:
    root = Path(__file__).resolve().parents[1]
    doc = parse_case_file(root / "cases" / "example_baidu.md")
    assert doc.id == "baidu_search_apple"
    assert "baidu.com" in doc.target
    assert len(doc.steps) >= 3
    assert len(doc.asserts) >= 1
