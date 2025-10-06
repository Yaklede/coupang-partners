from __future__ import annotations

from typing import List, Dict, Any, Optional

from .openai_client import chat_json


SYSTEM = (
    "당신은 한국 이커머스 상품 큐레이터입니다. 네이버 검색 트렌드 신호를 참고해 '지금 인기' 제품을 추천합니다."
)


def recommend_products_from_keywords(model: str, seed_keywords: List[str], count: int = 10, trend_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    if not seed_keywords:
        return []
    ctx = trend_context or {"keywords": [{"keyword": k} for k in seed_keywords]}
    import json as _json
    user = (
        "입력: 네이버 검색 트렌드 요약(JSON).\n"
        "요구: 지금 시점에 수요가 높은 '구체적 상품명' 10개 추천.\n"
        "지침:\n"
        "- 브랜드/모델/용량 등 구체명 위주(2~6어절).\n"
        "- 민감/금지 카테고리 제외(의약품/성인/주류/니코틴/의료기기).\n"
        "- 각 항목은 쿠팡 검색용 쿼리도 함께 제공(예: '브랜드 모델명 00L').\n"
        "- 출력 JSON: products[{name, search_query, reason}]\n"
        f"[NAVER_TREND]\n{_json.dumps(ctx, ensure_ascii=False)}\n"
    )
    try:
        out = chat_json(model=model, system=SYSTEM, user=user, temperature=0.6, max_tokens=800)
        items = out.get("products") or []
        res: List[Dict[str, Any]] = []
        for it in items:
            name = (it.get("name") or "").strip()
            if not name:
                continue
            res.append({
                "name": name,
                "search_query": (it.get("search_query") or name).strip(),
                "reason": it.get("reason", ""),
            })
            if len(res) >= count:
                break
        return res
    except Exception:
        # fallback: just echo keywords as names
        return [{"name": k, "reason": "trend seed"} for k in seed_keywords[:count]]
