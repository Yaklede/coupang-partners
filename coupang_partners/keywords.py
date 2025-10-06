from __future__ import annotations

import datetime as dt
import random
from typing import List

from .config import Settings
from .openai_client import chat_json


SYSTEM = (
    "당신은 한국어 마케팅/SEO 비서입니다. 네이버 블로그에 적합한 상업 의도 키워드를 제안합니다."
)


def generate_keywords(settings: Settings) -> List[str]:
    count = settings.keywords.daily_count if settings and settings.keywords else 3
    seed_categories = settings.keywords.seed_categories or ["가전", "주방", "리빙", "디지털"]

    # Build a simple seasonal hint
    month = dt.datetime.now().month
    season_hint = (
        "겨울" if month in (12, 1, 2) else "봄" if month in (3, 4, 5) else "여름" if month in (6, 7, 8) else "가을"
    )

    try:
        payload = chat_json(
            model=settings.providers.openai_model,
            system=SYSTEM,
            user=(
                "다음 조건으로 한국어 키워드만 JSON으로 반환하세요.\n"
                f"- 개수: {count}\n"
                f"- 카테고리 힌트: {', '.join(seed_categories)}\n"
                f"- 시즌 힌트: {season_hint}\n"
                "- 제약: 의약품/성인/주류/니코틴/의료기기 제외, 너무 일반적인 단일 키워드(예: '청소') 배제, 2~4어절 롱테일을 선호.\n"
                '{"keywords": ["..."]} 형태로만 응답하세요.'
            ),
            temperature=0.7,
            max_tokens=400,
        )
        kws = [k.strip() for k in payload.get("keywords", []) if isinstance(k, str)]
        kws = [k for k in kws if 2 <= len(k) <= 30]
        if kws:
            return kws[:count]
    except Exception:
        pass

    # Fallback list from config or defaults
    fallback = settings.keywords.fallback_list or ["가습기", "제습기", "무선 청소기", "에어프라이어", "전기포트"]
    random.shuffle(fallback)
    return fallback[:count]
