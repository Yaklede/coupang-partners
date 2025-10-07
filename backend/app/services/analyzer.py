from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from app.services.ai_client import complete_chat


ANALYZER_SYSTEM = (
    "역할: 전자상거래 상품 정렬기. 입력(브랜드/모델 추정, 쿠팡 상세 URL/HTML alt/요약)을 분석해 블로그 작성 정합성을 보장하는 JSON을 생성한다.\n"
    "출력은 반드시 JSON 객체 하나. 코드블록/설명 금지. 키: \n"
    "- enforce_product_name: 최종 본문에 써야 할 정확 표기(예: '로지텍 G PRO X SUPERLIGHT 2').\n"
    "- allowed_names: 허용 가능한 동의 표기/별칭 배열(브랜드+모델 변주 포함).\n"
    "- category: 상위 카테고리(예: '게이밍 마우스').\n"
    "- spec_keys: 비교/요약에 유용한 스펙 키 배열(예: '무게(그램)','센서','DPI','폴링레이트','연결','배터리','크기').\n"
    "- disallowed_brands: 언급하지 말아야 할 브랜드/라인업 키워드(경쟁사 일반명).\n"
    "- link_anchors: 링크 앵커 문구 후보 3~5개(자연어, 명령형 금지).\n"
)


def _extract_alt_names(affiliate_html: str | None) -> List[str]:
    if not affiliate_html:
        return []
    alts = re.findall(r'alt="([^"]+)"', affiliate_html or '')
    out: List[str] = []
    for a in alts:
        t = a.strip()
        if t and t not in out:
            out.append(t)
    return out[:5]


async def analyze_alignment(
    *,
    brand: str | None,
    model: str | None,
    title_guess: str | None,
    affiliate_url: str | None,
    affiliate_html: str | None,
    keyword: str | None,
) -> Dict[str, Any]:
    alt_names = _extract_alt_names(affiliate_html)
    hint = {
        "brand": brand or "",
        "model": model or "",
        "title_guess": title_guess or "",
        "keyword": keyword or "",
        "affiliate_url": affiliate_url or "",
        "alt_names": alt_names,
    }
    user = (
        "입력 힌트:\n" + str(hint) + "\n\n"
        "요구사항:\n"
        "- enforce_product_name은 가장 정확하고 자연스러운 한국어 표기. 약어나 비공식 표기는 allowed_names로.\n"
        "- allowed_names는 브랜드+모델의 다양한 실사용 표기 4~8개 수록.\n"
        "- category는 3~5어절.\n"
        "- spec_keys는 이 카테고리에서 전형적으로 비교하는 항목 6~10개.\n"
        "- disallowed_brands는 동급 경쟁사 메이저 라인업 이름(5~8개). 본문에서 제거해야 함.\n"
        "- link_anchors는 과한 상업어구 없이 자연스러운 정보 탐색형 문구.\n"
    )
    text, _ = await complete_chat(
        messages=[
            {"role": "system", "content": ANALYZER_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        max_tokens=800,
        purpose='small',
        force_json=True,
    )
    # simple JSON parse (we expect obj)
    import json
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    # fallback minimal
    name = (brand or '') + ' ' + (model or '')
    return {
        "enforce_product_name": name.strip() or (title_guess or keyword or "제품"),
        "allowed_names": list(filter(None, [name.strip(), title_guess, keyword])),
        "category": "게이밍 마우스",
        "spec_keys": ["무게(그램)", "센서", "DPI", "폴링레이트", "연결", "배터리", "크기"],
        "disallowed_brands": ["G304", "Viper", "DeathAdder", "Model O"],
        "link_anchors": ["자세히 보기", "상세 스펙·최저가 확인", "오늘 가격/재고 확인"],
    }

