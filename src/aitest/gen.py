from __future__ import annotations

import ast
import re
from pathlib import Path

from aitest.case_parser import parse_case_file
from aitest.llm.client import chat_completion
from aitest.llm.prompts import build_gen_prompt

_FORBIDDEN_CALLS = ("eval(", "exec(", "compile(", "os.system")


def _forbidden_import_roots() -> frozenset[str]:
    return frozenset({"subprocess", "socket", "urllib", "requests", "httpx", "ftplib"})


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z0-9]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def _validate_generated_code(src: str) -> None:
    tree = ast.parse(src)
    roots = _forbidden_import_roots()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base = (alias.name or "").split(".")[0]
                if base in roots:
                    raise ValueError(f"Forbidden import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            base = mod.split(".")[0] if mod else ""
            if base in roots:
                raise ValueError(f"Forbidden import from: {mod}")
    for bad in _FORBIDDEN_CALLS:
        if bad in src:
            raise ValueError(f"Generated code contains forbidden pattern: {bad!r}")


def run_gen(case_path: Path, out_dir: Path | None = None) -> Path:
    doc = parse_case_file(case_path.resolve())
    out = out_dir or Path("tests/generated")
    out.mkdir(parents=True, exist_ok=True)
    out_file = out / f"test_{doc.id}.py"

    user_prompt = build_gen_prompt(doc)
    messages = [
        {
            "role": "system",
            "content": "You output only valid Python test code for Playwright+pytest. No markdown fences.",
        },
        {"role": "user", "content": user_prompt},
    ]
    raw = chat_completion(messages)
    code = _strip_fences(raw)
    _validate_generated_code(code)
    out_file.write_text(code + "\n", encoding="utf-8")
    return out_file
