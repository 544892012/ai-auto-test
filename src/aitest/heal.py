from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from aitest.llm.client import chat_completion
from aitest.llm.prompts import build_heal_prompt


def run_heal(
    *,
    case_id: str,
    generated_dir: Path | None = None,
    reports_dir: Path | None = None,
) -> Path:
    gen_dir = generated_dir or Path("tests/generated")
    rep_dir = reports_dir or Path("reports")
    py_path = gen_dir / f"test_{case_id}.py"
    fail_path = rep_dir / "last_failure.txt"
    if not py_path.is_file():
        raise FileNotFoundError(f"Missing generated test: {py_path}")
    if not fail_path.is_file():
        raise FileNotFoundError(
            f"Missing {fail_path}; run tests to produce failure log first."
        )
    generated_py = py_path.read_text(encoding="utf-8")
    failure_log = fail_path.read_text(encoding="utf-8")
    prompt = build_heal_prompt(
        case_id=case_id,
        generated_py=generated_py,
        failure_log=failure_log[:120_000],
    )
    messages = [
        {
            "role": "system",
            "content": "You output only a unified diff. No markdown, no prose.",
        },
        {"role": "user", "content": prompt},
    ]
    diff = chat_completion(messages, temperature=0.1)
    rep_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = rep_dir / f"heal-{case_id}-{ts}.diff"
    out.write_text(diff.strip() + "\n", encoding="utf-8")
    return out
