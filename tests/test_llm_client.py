from __future__ import annotations

import pytest

from aitest.llm.client import chat_completion


def test_chat_completion_uses_env_and_returns_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test")
    monkeypatch.setenv("LLM_API_KEY", "secret")
    monkeypatch.setenv("LLM_MODEL", "m1")

    class FakeResp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"choices": [{"message": {"content": " hello "}}]}

    class FakeClient:
        def __init__(self, timeout: float = 120.0) -> None:
            self.timeout = timeout

        def __enter__(self) -> FakeClient:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(self, url: str, **kwargs: object) -> FakeResp:
            assert url == "https://example.test/v1/chat/completions"
            return FakeResp()

    monkeypatch.setattr("httpx.Client", FakeClient)
    out = chat_completion([{"role": "user", "content": "ping"}])
    assert out == "hello"
