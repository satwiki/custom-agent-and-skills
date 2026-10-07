"""Chat completions via the OpenAI SDK using EVAL_ENDPOINT, EVAL_API_KEY, and EVAL_MODEL."""

from __future__ import annotations

import json
import os
import re
import time

from openai import AzureOpenAI, OpenAI


def _client() -> AzureOpenAI | OpenAI:
    """Foundry /openai/v1 URLs use OpenAI. Classic Azure uses AzureOpenAI."""
    timeout = float(os.environ.get("EVAL_TIMEOUT_SECONDS", "120"))
    key = os.environ["EVAL_API_KEY"]
    endpoint = os.environ["EVAL_ENDPOINT"].rstrip("/")
    version = os.environ.get("EVAL_API_VERSION", "").strip()
    if "/openai/v1" in endpoint or not version:
        return OpenAI(api_key=key, base_url=endpoint, timeout=timeout)
    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=key,
        api_version=version,
        timeout=timeout,
    )


def complete(messages: list[dict[str, str]]) -> dict:
    """Return {text, error, duration_ms, input_tokens, output_tokens}."""
    started = time.perf_counter()
    try:
        response = _client().chat.completions.create(
            model=os.environ["EVAL_MODEL"],
            messages=messages,
            temperature=0,
        )
    except Exception as error:
        return _empty(started, str(error))
    duration_ms = int((time.perf_counter() - started) * 1000)
    choice = response.choices[0] if response.choices else None
    content = choice.message.content if choice and choice.message else None
    text = content.strip() if isinstance(content, str) else ""
    usage = response.usage
    return {
        "text": text,
        "error": None if text else "Empty assistant message",
        "duration_ms": duration_ms,
        "input_tokens": None if usage is None else usage.prompt_tokens,
        "output_tokens": None if usage is None else usage.completion_tokens,
    }


def parse_judge(text: str) -> list[dict]:
    """Read {"items": [...]} from a model reply."""
    stripped = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*([\s\S]*?)\s*```", stripped)
    if fenced:
        stripped = fenced.group(1).strip()
    start, end = stripped.find("{"), stripped.rfind("}")
    payload = json.loads(stripped[start : end + 1])
    items = payload["items"]
    if not isinstance(items, list):
        raise ValueError("Judge JSON must contain an items array")
    return items


def _empty(started: float, error: str) -> dict:
    """Empty chat result used when the HTTP call fails."""
    return {
        "text": "",
        "error": error,
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "input_tokens": None,
        "output_tokens": None,
    }
