from __future__ import annotations

from typing import List, Dict, Any

from .openai_client import chat_json


SYSTEM = (
    "당신은 한국 이커머스 상품 큐레이터입니다. 입력된 검색 트렌드 키워드를 참고해 쿠팡에서 구매 의도가 높은 구체적인 상품 후보를 추천하세요."
)


def recommend_products_from_keywords(model: str, seed_keywords: List[str], count: int = 10) -> List[Dict[str, Any]]:
    if not seed_keywords:
        return []
    user = (
        "다음 키워드들을 참고해 한국 소비자 관점에서 실제로 검색/구매할 법한 구체적인 상품명 10개를 추천하세요.\n"
        "- 원칙: 브랜드 혹은 모델이 드러나는 2~6어절의 구체명 위주\n"
        "- 민감/금지 카테고리 제외(의약품/성인/주류/니코틴/의료기기)\n"
        "- 출력은 JSON, 필드: products[{name, reason}]\n"
        f"키워드: {', '.join(seed_keywords)}\n"
    )
    try:
        out = chat_json(model=model, system=SYSTEM, user=user, temperature=0.6, max_tokens=800)
        items = out.get("products") or []
        res: List[Dict[str, Any]] = []
        for it in items:
            name = (it.get("name") or "").strip()
            if not name:
                continue
            res.append({"name": name, "reason": it.get("reason", "")})
            if len(res) >= count:
                break
        return res
    except Exception:
        # fallback: just echo keywords as names
        return [{"name": k, "reason": "trend seed"} for k in seed_keywords[:count]]

