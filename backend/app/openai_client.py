"""Shared OpenAI client for structured JSON intelligence tasks."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


async def call_openai_json(
    system_prompt: str,
    user_payload: dict[str, Any],
    *,
    temperature: float = 0.2,
    max_tokens: int = 2500,
) -> dict[str, Any] | None:
    """Call OpenAI with JSON response format. Returns parsed dict or None on failure."""
    if not OPENAI_API_KEY:
        return None

    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(user_payload, default=str)},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            },
        )
        data = resp.json()
        if "error" in data:
            return None
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
