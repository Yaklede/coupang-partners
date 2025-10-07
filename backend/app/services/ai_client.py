from typing import Any, Dict, List, Tuple
from app.settings import settings
from app.services.openai_client import complete_chat as openai_complete
from app.services.gemini_client import complete_chat_gemini
from app.services.config import get_ai_config_dict


async def complete_chat(
    *,
    messages: List[Dict[str, Any]],
    temperature: float | None = 1.0,
    max_tokens: int | None = None,
    use: str | None = None,  # 'gpt' | 'gemini'
    purpose: str = 'small',  # 'small' | 'writer'
    force_json: bool = False,
) -> Tuple[str, int | None]:
    cfg = await get_ai_config_dict()
    provider = (use or cfg.get('ai_provider') or settings.AI_PROVIDER).lower()
    if provider == 'gemini':
        model = cfg.get('gemini_model_writer' if purpose == 'writer' else 'gemini_model_small') or (
            settings.GEMINI_MODEL_WRITER if purpose == 'writer' else settings.GEMINI_MODEL_SMALL
        )
        # Per request: do NOT enforce token limits on Gemini
        return await complete_chat_gemini(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=None,
            force_json=force_json,
        )
    else:
        model = cfg.get('openai_model_writer' if purpose == 'writer' else 'openai_model_small') or (
            settings.OPENAI_MODEL_WRITER if purpose == 'writer' else settings.OPENAI_MODEL_SMALL
        )
        return openai_complete(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens, force_json=force_json)
