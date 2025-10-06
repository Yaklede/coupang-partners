from __future__ import annotations

import json
from typing import Dict, Any, List

from jinja2 import Template

from .openai_client import chat_text


WRITER_SYSTEM = (
    "역할: 당신은 한국어 쇼핑 블로거입니다. 사람처럼 씁니다. 광고임을 숨기지 않되 과장하지 않습니다.\n"
    "규칙:\n"
    "1) 입력 JSON의 사실만 사용.\n"
    "2) 한 문단에 2~4문장, 문장 길이 다양화. 반복어구 금지.\n"
    "3) 단점 1~2개, 관리 팁 1개 이상 포함.\n"
    "4) 개인적 맥락 1회: '원룸/아이방/반려동물' 등 상황 가정.\n"
    "5) 이해를 돕는 비교 1회(동급/이전 모델 차이). 욕설·과장은 금지.\n"
    "6) 끝에 투명 고지문과 제휴 링크 버튼 문구 포함.\n"
    "출력: 네이버 블로그용 HTML(강조는 <strong>, 소제목은 <h3>). 표는 <table> 사용.\n"
    "어조: 담백, 생활감 있는 한국어, 리뷰어 톤."
)


REFINER_SYSTEM = (
    "역할: 텍스트 에디터. AI 흔적(상투적 연결어, 과한 매끈함)을 줄이고 한국어 생활 감각을 살립니다.\n"
    "반복 어구 제거, 조사·접속사 다양화, 근거 없는 절대 표현 축소, 단락 첫 문장에 미세 훅 추가.\n"
    "반환: HTML 보존, 의미 불변."
)


SEO_SYSTEM = (
    "입력: 게시 전 HTML, 키워드 리스트.\n"
    "작업: H2/H3 소제목에 롱테일 키워드 1~2개 자연 삽입, 본문 초반 150자에 핵심 키워드 1회, 메타 설명 80~110자, 해시태그 6~10개, 키워드 과밀도 2% 이하.\n"
    "반환: title, description, hashtags[], 개선된 HTML."
)


DISCLOSURE_HTML = (
    '<p style="font-size:12px;color:#777">* 이 글에는 쿠팡 파트너스 활동을 통해 일정액의 수수료를 제공받을 수 있는 링크가 포함되어 있습니다.</p>'
)


def build_rag(product: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "product": {
            "id": product.get("id"),
            "title": product.get("title"),
            "brand": product.get("brand"),
            "category": product.get("category", []),
            "price": product.get("price"),
            "sale_rate": product.get("sale_rate"),
            "rating": product.get("rating"),
            "review_cnt": product.get("review_cnt"),
            "specs": product.get("specs", {}),
            "pros": product.get("pros", []),
            "cons": product.get("cons", []),
            "best_for": product.get("best_for", []),
            "images": product.get("images", []),
            "deeplink": product.get("deeplink"),
        },
        "compares": [],
        "tips": [],
        "seasonality": "",
        "faq": [],
    }


def write_post(model: str, rag_json: Dict[str, Any]) -> str:
    user = (
        "[컨텍스트]\n" + json.dumps(rag_json, ensure_ascii=False) +
        "\n[생성 지시]\n- 제목: 35자 내외, 검색 의도 반영, 모델명 노출 가급적 1회.\n"
        "- 도입: 문제상황→제품 해결 포인트 2줄.\n"
        "- 본문: 장점(2~3), 단점(1~2), 사용팁(1~2), 간단 비교(1), 핵심 스펙 표(있으면).\n"
        "- 마무리: 어떤 사람에게 맞는지, 주의점 1줄.\n"
        "- CTA: \"자세히 보기\" 링크 버튼(제휴 링크 주입).\n"
        "[제약]\n- 의학적·법적 효능 금지, 과도한 이모지 금지(총 0~2개), 영어 남용 금지.\n- 문장 길이 다양화(짧은 문장 20~30%), 문체 혼합(서술체/구어체 7:3).\n"
    )
    html = chat_text(model=model, system=WRITER_SYSTEM, user=user, temperature=0.7, max_tokens=1400)
    return html


def refine_post(model: str, html: str) -> str:
    user = f"다음 HTML을 자연스러운 한국어로 리라이팅하세요. 의미와 구조는 유지하세요.\n---\n{html}"
    return chat_text(model=model, system=REFINER_SYSTEM, user=user, temperature=0.5, max_tokens=1200)


def seo_optimize(model: str, html: str, keywords: List[str]) -> Dict[str, Any]:
    user = (
        json.dumps({"html": html, "keywords": keywords}, ensure_ascii=False)
    )
    out = chat_text(model=model, system=SEO_SYSTEM, user=user, temperature=0.4, max_tokens=900)
    # Best-effort parse: expect JSON fields, but allow plain text fallback
    try:
        data = json.loads(out)
        return {
            "title": data.get("title"),
            "description": data.get("description"),
            "hashtags": data.get("hashtags", []),
            "html": data.get("html") or data.get("improved_html") or html,
        }
    except Exception:
        return {"title": None, "description": None, "hashtags": keywords[:6], "html": html}


def inject_disclosure(html: str) -> str:
    return html + "\n" + DISCLOSURE_HTML


def ensure_cta(html: str, deeplink: str) -> str:
    if not deeplink:
        return html
    import re
    # If no link present to deeplink, append a CTA button.
    if deeplink not in html:
        cta = f'\n<p><a href="{deeplink}" target="_blank" rel="nofollow">자세히 보기</a></p>'
        return html + cta
    return html


def render_minimal_html(product: Dict[str, Any]) -> str:
    tpl = Template(
        """
        <h2>{{ title }}</h2>
        <p>{{ intro }}</p>
        {% if price %}<p><strong>가격:</strong> {{ price }}원</p>{% endif %}
        {% if rating %}<p><strong>평점:</strong> {{ rating }} (리뷰 {{ review_cnt or 0 }}개)</p>{% endif %}
        {% if specs %}
        <h3>핵심 스펙</h3>
        <table>
          <tr><th>항목</th><th>내용</th></tr>
          {% for k, v in specs.items() %}
          <tr><td>{{ k }}</td><td>{{ v }}</td></tr>
          {% endfor %}
        </table>
        {% endif %}
        {% if deeplink %}<p><a href="{{ deeplink }}" target="_blank" rel="nofollow">자세히 보기</a></p>{% endif %}
        """
    )
    return tpl.render(
        title=product.get("title") or "제품 소개",
        intro="간단 요약 및 소개",
        price=product.get("price"),
        rating=product.get("rating"),
        review_cnt=product.get("review_cnt"),
        specs=product.get("specs") or {},
        deeplink=product.get("deeplink") or product.get("url"),
    )
