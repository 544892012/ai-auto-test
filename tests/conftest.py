from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    return {**browser_context_args, "locale": "zh-CN"}


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):  # noqa: ANN001
    outcome = yield
    rep = outcome.get_result()
    if rep.outcome != "failed" or call.when != "call":
        return
    lines: list[str] = [rep.nodeid, str(rep.longrepr)]
    page = item.funcargs.get("page")
    if page is not None:
        try:
            html = page.content()
            lines.append(html[:8000])
        except Exception as exc:  # noqa: BLE001 — 诊断用途
            lines.append(f"(page.content failed: {exc})")
    root = Path(__file__).resolve().parents[1]
    rep_dir = root / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    (rep_dir / "last_failure.txt").write_text("\n\n---\n\n".join(lines), encoding="utf-8")
