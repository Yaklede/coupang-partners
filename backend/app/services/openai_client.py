from app.settings import settings
from openai import OpenAI
from typing import Any, Dict, List, Tuple


def get_client() -> OpenAI | None:
    if not settings.OPENAI_API_KEY:
        return None
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def complete_chat(
    *,
    model: str,
    messages: List[Dict[str, Any]],
    temperature: float | None = 1.0,
    max_tokens: int | None = None,
    force_json: bool = False,
) -> Tuple[str, int | None]:
    """Create a chat completion, adapting to models that reject some params.

    - If max_tokens is unsupported → retry without it.
    - If temperature != 1 is unsupported → retry without temperature (defaults to model's).

    Returns (text, total_tokens). Raises on final failure.
    """
    client = get_client()
    if not client:
        raise RuntimeError("OPENAI_API_KEY not configured")

    allow_max = max_tokens is not None
    allow_temp = temperature is not None

    last_err: Exception | None = None
    for _ in range(3):
        try:
            kwargs: Dict[str, Any] = dict(model=model, messages=messages)
            if allow_temp and temperature is not None:
                kwargs["temperature"] = temperature
            if allow_max and max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            if force_json:
                # prefer strict json mode if supported
                kwargs["response_format"] = {"type": "json_object"}
            resp = client.chat.completions.create(**kwargs)
            text = (resp.choices[0].message.content or "").strip()
            total = int(getattr(resp, "usage", None).total_tokens) if getattr(resp, "usage", None) else None
            return text, total
        except Exception as e:
            s = str(e)
            last_err = e
            if allow_max and "max_tokens" in s and ("Unsupported parameter" in s or "unsupported_parameter" in s):
                allow_max = False
                continue
            if allow_temp and "temperature" in s and ("Unsupported value" in s or "unsupported_value" in s):
                allow_temp = False
                continue
            if force_json and ("response_format" in s or "json" in s):
                # retry without enforced json mode
                force_json = False
                continue
            break
    # If we reach here, all retries failed
    raise last_err if last_err else RuntimeError("OpenAI completion failed")
