from __future__ import annotations
from typing import List
from loguru import logger
from app.services.ai_client import complete_chat


REPAIR_SYSTEM = (
    "역할: JSON 데이터 정제기. 입력 텍스트에서 제품 후보 목록을 추출해 올바른 JSON으로 변환.\n"
    "규칙:\n"
    "- 출력은 '반드시' JSON만. 코드블록/설명/주석 금지.\n"
    "- 최종 형식: JSON 배열([..]) 또는 {\"items\":[..]} 중 하나. 배열 원소는 객체여야 함.\n"
    "- 각 객체 키: title_guess, brand, model, price_band, why, image_hint, coupang_url. 값은 문자열 또는 null.\n"
    "- 항목 수: 5~12개. 불분명하면 최대한 합리적으로 채움.\n"
)


async def attempt_repair_to_items_array(raw_text: str) -> str:
    """Ask the model to convert arbitrary text into a strict JSON array/object with items.
    Returns JSON string (or empty string if still impossible).
    """
    try:
        text, _ = await complete_chat(
            messages=[
                {"role": "system", "content": REPAIR_SYSTEM},
                {"role": "user", "content": f"다음 텍스트를 요구 포맷의 JSON으로 변환:\n\n{raw_text}\n\n출력은 JSON만."},
            ],
            temperature=0.0,
            max_tokens=1200,
            purpose='small',
            force_json=True,
        )
        return text or ""
    except Exception as e:
        logger.warning("JSON repair failed: {}", e)
        return ""

