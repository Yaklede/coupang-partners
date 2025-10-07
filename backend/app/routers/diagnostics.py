from fastapi import APIRouter
from app.settings import settings
from app.services.ai_client import complete_chat

router = APIRouter()


@router.get("/ai")
async def ai_status():
    from app.services.config import get_ai_config_dict
    cfg = await get_ai_config_dict()
    info = {
        "provider": cfg.get('ai_provider'),
        "model_small": cfg.get('openai_model_small') if cfg.get('ai_provider')=='gpt' else cfg.get('gemini_model_small'),
        "model_writer": cfg.get('openai_model_writer') if cfg.get('ai_provider')=='gpt' else cfg.get('gemini_model_writer'),
        "has_api_key": bool(settings.OPENAI_API_KEY) if cfg.get('ai_provider')=='gpt' else bool(settings.GEMINI_API_KEY),
    }
    try:
        _, total = await complete_chat(messages=[{"role":"user","content":"ping"}], temperature=None, max_tokens=2, purpose='small')
        info.update({
            "ok": True,
            "total_tokens": total,
        })
    except Exception as e:
        info.update({"ok": False, "reason": f"AI error: {e}"})
    return info
