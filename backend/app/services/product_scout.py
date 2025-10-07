import json
from slugify import slugify
from app.settings import settings
from app.services.ai_client import complete_chat
from app.utils.json_parse import parse_json_array_loose, parse_json_items_or_array, salvage_json_items_from_truncated
from loguru import logger
from app.utils.errors import AIError
from app.utils.urls import build_coupang_search_url
from app.services.coupang import fetch_top_product_url
from app.services.json_repair import attempt_repair_to_items_array
from app.db import AsyncSessionLocal
from app.services.budget import add_usage


SYSTEM_PROMPT = (
    "당신은 이커머스 MD입니다. 사용자가 준 검색어(네이버 이용자 관점)와 쇼핑 의도를 바탕으로, "
    "쿠팡에서 잘 팔릴 법한 상품 후보를 5~8개 제안하세요.\n"
    "'반드시' JSON만 출력하세요. 코드블록/설명/주석/앞뒤 텍스트 금지.\n"
    "출력 형식: JSON 배열([..]) 또는 {\"items\":[..]} 객체 중 하나.\n"
    "각 항목은 {\"title_guess\",\"brand\",\"model\",\"price_band\",\"why\",\"image_hint\",\"coupang_url\"}를 포함.\n"
    "이미 판매 종결/단종/사기성 제품은 제외. 동일 모델 변형은 1~2개만."
)


async def recommend_products(keyword: str, dedupe_keys: list[str]) -> list[dict]:
    # provider selection handled in ai_client.complete_chat via config

    user_msg = f"키워드: \"{keyword}\"\n내가 이미 올린 상품 dedupe 키 목록: {dedupe_keys}\n가격대 범위: 자유"
    try:
        text, total_tokens = await complete_chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=1200,
            purpose='small',
            force_json=True,
        )
    except Exception as e:
        msg = str(e)
        logger.exception("AI completion error in ProductScout")
        if 'not configured' in msg:
            raise AIError("config_error", msg)
        if 'policy_block' in msg or 'blocked' in msg:
            raise AIError("policy_block", msg)
        raise AIError("network_error", f"AI API request failed: {e}")
    if not text:
        raise AIError("empty_response", "OpenAI returned no content")
    logger.debug("ProductScout raw response (truncated): {}", text[:1200])
    # budget tracking (approx)
    async with AsyncSessionLocal() as session:
        await add_usage(session, total_tokens)
    data = parse_json_array_loose(text) or parse_json_items_or_array(text)
    if not data:
        # Try salvage from truncated JSON first
        salvage = salvage_json_items_from_truncated(text)
        if salvage:
            logger.warning("Parsed %d items via salvage parser from truncated JSON", len(salvage))
            data = salvage
        else:
            logger.warning("Failed to parse model JSON. Trying repair pass...")
            fixed = await attempt_repair_to_items_array(text)
            data = parse_json_array_loose(fixed) or parse_json_items_or_array(fixed) or salvage_json_items_from_truncated(fixed)
            if not data:
                logger.error("JSON repair failed. Sample: {}", (text or "")[:300])
                raise AIError("parse_error", "Model did not return a valid JSON array/object with items as instructed")
        fixed = await attempt_repair_to_items_array(text)
        data = parse_json_array_loose(fixed) or parse_json_items_or_array(fixed)
        if not data:
            logger.error("JSON repair failed. Sample: {}", (text or "")[:300])
            raise AIError("parse_error", "Model did not return a valid JSON array/object with items as instructed")
    for d in data:
        d["dedupe_key"] = slugify(f"{d.get('brand','')}-{d.get('model','')}-{keyword}")
        if not d.get("coupang_url"):
            query = (d.get('brand') or '') + ' ' + (d.get('model') or '')
            query = query.strip() or (d.get('title_guess') or keyword)
            product_url = None
            if settings.COUPANG_SCRAPE:
                try:
                    product_url = await fetch_top_product_url(query, timeout=float(settings.COUPANG_SCRAPE_TIMEOUT))
                except Exception:
                    product_url = None
            d["coupang_url"] = product_url or build_coupang_search_url(
                title_guess=d.get('title_guess'), brand=d.get('brand'), model=d.get('model'), keyword=keyword
            )
    return data
