from __future__ import annotations

import os
from typing import Optional, Dict, Any, List

from openai import OpenAI


def get_openai_client() -> OpenAI:
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)


def chat_json(model: str, system: str, user: str, temperature: float = 0.7, max_tokens: int = 800) -> Dict[str, Any]:
    client = get_openai_client()
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
    )
    content = resp.choices[0].message.content or "{}"
    import json

    return json.loads(content)


def chat_text(model: str, system: str, user: str, temperature: float = 0.6, max_tokens: int = 1200) -> str:
    client = get_openai_client()
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""

