from __future__ import annotations

import os
from typing import Any

import httpx


def chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    temperature: float = 0.2,
    timeout: float = 120.0,
) -> str:
    """Call OpenAI-compatible POST {base}/v1/chat/completions."""
    base = (
        base_url
        or os.environ.get("LLM_BASE_URL")
        or os.environ.get("OPENAI_API_BASE")
        or ""
    ).rstrip("/")
    key = (
        api_key
        or os.environ.get("LLM_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("DEEPSEEK_API_KEY")
        or ""
    )
    mdl = model or os.environ.get("LLM_MODEL") or os.environ.get("OPENAI_MODEL") or ""
    if not mdl and "deepseek" in base.lower():
        mdl = "deepseek-chat"
    if not base or not mdl:
        raise RuntimeError(
            "Set LLM_BASE_URL (or OPENAI_API_BASE) and LLM_MODEL (or OPENAI_MODEL), "
            "or use a DeepSeek-compatible base URL to default model to deepseek-chat."
        )
    url = f"{base}/v1/chat/completions"
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    payload: dict[str, Any] = {
        "model": mdl,
        "messages": messages,
        "temperature": temperature,
    }
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"LLM response missing choices: {data!r:.500}")
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(f"LLM empty content: {data!r:.500}")
    return content.strip()
