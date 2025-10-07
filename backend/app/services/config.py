from __future__ import annotations
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import AsyncSessionLocal
from app.models import AppConfig
from app.settings import settings


async def get_ai_config_dict() -> Dict[str, str]:
    values: Dict[str, str] = {}
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(AppConfig))
        for row in res.scalars():
            values[row.key] = row.value or ""
    # fallbacks from env
    return {
        'ai_provider': values.get('ai_provider', settings.AI_PROVIDER),
        'openai_model_small': values.get('openai_model_small', settings.OPENAI_MODEL_SMALL),
        'openai_model_writer': values.get('openai_model_writer', settings.OPENAI_MODEL_WRITER),
        'gemini_model_small': values.get('gemini_model_small', settings.GEMINI_MODEL_SMALL),
        'gemini_model_writer': values.get('gemini_model_writer', settings.GEMINI_MODEL_WRITER),
        'gemini_safety': values.get('gemini_safety', settings.GEMINI_SAFETY),
    }


async def set_ai_config_dict(data: Dict[str, str]):
    allowed = {'ai_provider', 'openai_model_small', 'openai_model_writer', 'gemini_model_small', 'gemini_model_writer', 'gemini_safety'}
    async with AsyncSessionLocal() as session:
        for k, v in data.items():
            if k not in allowed:
                continue
            existing = await session.get(AppConfig, k)
            if existing:
                existing.value = str(v)
            else:
                session.add(AppConfig(key=k, value=str(v)))
        await session.commit()
