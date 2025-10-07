from typing import Any, Dict, List, Tuple
import google.generativeai as genai
from app.settings import settings
from app.services.config import get_ai_config_dict


def get_client() -> bool:
    if not settings.GEMINI_API_KEY:
        return False
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return True


async def complete_chat_gemini(
    *,
    model: str,
    messages: List[Dict[str, Any]],
    temperature: float | None = 1.0,
    max_tokens: int | None = None,
    force_json: bool = False,
) -> Tuple[str, int | None]:
    if not get_client():
        raise RuntimeError("GEMINI_API_KEY not configured")
    # Flatten messages to a single prompt; prefer system then user/assistant order
    sys = "\n\n".join(m["content"] for m in messages if m.get("role") == "system")
    user_parts = [m["content"] for m in messages if m.get("role") != "system"]
    prompt = (sys + "\n\n" if sys else "") + "\n\n".join(user_parts)

    generation_config = {}
    if temperature is not None:
        generation_config["temperature"] = temperature
    if max_tokens is not None:
        generation_config["max_output_tokens"] = max_tokens
    if force_json:
        generation_config["response_mime_type"] = "application/json"

    # Safety from config
    cfg = await get_ai_config_dict()
    safety_mode = (cfg.get('gemini_safety') or settings.GEMINI_SAFETY or 'low').lower()
    threshold = 'BLOCK_ONLY_HIGH' if safety_mode == 'low' else ('BLOCK_NONE' if safety_mode == 'none' else 'BLOCK_MEDIUM_AND_ABOVE')
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": threshold},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": threshold},
        {"category": "HARM_CATEGORY_SEXUAL", "threshold": threshold},
        {"category": "HARM_CATEGORY_DANGEROUS", "threshold": threshold},
    ]

    model_obj = genai.GenerativeModel(model)
    try:
        resp = model_obj.generate_content(prompt, generation_config=generation_config or None, safety_settings=safety_settings)
    except Exception as e:
        # Retry without unsupported params
        s = str(e)
        if "temperature" in s:
            generation_config.pop("temperature", None)
        if "max_output_tokens" in s:
            generation_config.pop("max_output_tokens", None)
        resp = model_obj.generate_content(prompt, generation_config=generation_config or None, safety_settings=safety_settings)

    # Extract usage
    total_tokens = None
    try:
        usage = getattr(resp, 'usage_metadata', None)
        if usage and getattr(usage, 'total_token_count', None) is not None:
            total_tokens = int(usage.total_token_count)
    except Exception:
        total_tokens = None

    # Extract text strictly from candidates/parts (never access resp.text)
    text = ''
    try:
        cands = getattr(resp, 'candidates', None) or []
        for c in cands:
            content = getattr(c, 'content', None)
            parts = getattr(content, 'parts', None) or []
            collected = []
            for p in parts:
                t = getattr(p, 'text', None)
                if t:
                    collected.append(t)
            if collected:
                text = ''.join(collected).strip()
                if text:
                    break
    except Exception:
        text = ''

    if not text:
        # Determine block/no-content reason
        reason = None
        try:
            pf = getattr(resp, 'prompt_feedback', None)
            if pf and getattr(pf, 'block_reason', None):
                reason = f"blocked: {pf.block_reason}"
                ratings = getattr(pf, 'safety_ratings', None) or []
                details = []
                for r in ratings:
                    try:
                        if getattr(r, 'blocked', False):
                            details.append(f"{getattr(r, 'category', 'harm')}: {getattr(r, 'probability', '')}")
                    except Exception:
                        continue
                if details:
                    reason += " (" + ", ".join(details) + ")"
        except Exception:
            reason = None
        if not reason:
            reason = "no candidates returned"
        raise RuntimeError(f"policy_block: {reason}")

    return text, total_tokens
