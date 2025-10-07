import random
from app.settings import settings
from app.services.ai_client import complete_chat
from app.db import AsyncSessionLocal
from app.services.budget import add_usage
from app.models import ProductCandidate
from app.utils.errors import AIError
from app.services.prompts import WRITER_SYSTEM, build_user_prompt


def _ensure_disclosure_and_link(text: str, affiliate_url: str) -> str:
    lines = [l.rstrip() for l in (text or "").splitlines()]
    if not lines:
        return text
    # Ensure first line starts with '# '
    first = lines[0].strip()
    if not first.startswith('# '):
        lines.insert(0, '# [광고/제휴] 제목')
    else:
        # ensure [광고/제휴] prefix in title
        title_txt = lines[0][2:].strip()
        if not title_txt.startswith('[광고/제휴]'):
            lines[0] = '# ' + '[광고/제휴] ' + title_txt
    disclosure = '*본 글은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.*'
    if len(lines) < 2 or disclosure not in lines[1]:
        lines.insert(1, disclosure)
    body = '\n'.join(lines)
    # Ensure 2~3 CTA links placed at strategic points without duplication
    cta_variants = [
        f"[자세히 보기]({affiliate_url})",
        f"[상세 스펙·최저가 확인]({affiliate_url})",
        f"[오늘 가격/재고 확인]({affiliate_url})",
    ]
    # Current count
    present = sum(1 for v in cta_variants if v in body)
    needed = max(0, 2 - present)
    if needed == 0:
        return body
    inserts: list[tuple[int, str]] = []
    # 1) After first paragraph (below disclosure)
    if needed > 0:
        pos = body.find('\n\n', body.find(disclosure) + len(disclosure))
        idx = pos if pos != -1 else len(body)
        inserts.append((idx, "\n\n" + cta_variants[0] + "\n"))
        needed -= 1
    # 2) After first table or after second H2
    if needed > 0:
        lines2 = body.splitlines()
        first_table_end = -1
        h2_indices = [i for i, l in enumerate(lines2) if l.startswith('## ')]
        # find table block
        in_table = False
        for i, l in enumerate(lines2):
            if l.startswith('|') and '|' in l:
                in_table = True
            elif in_table and l.strip() == '':
                first_table_end = i
                break
        if first_table_end != -1:
            # position after table block
            char_idx = sum(len(x) + 1 for x in lines2[:first_table_end])
            inserts.append((char_idx, "\n" + cta_variants[1] + "\n"))
        elif len(h2_indices) >= 2:
            char_idx = sum(len(x) + 1 for x in lines2[:h2_indices[1]])
            inserts.append((char_idx, "\n\n" + cta_variants[1] + "\n"))
        else:
            inserts.append((len(body), "\n\n" + cta_variants[1] + "\n"))
        needed -= 1
    # apply inserts in reverse index order
    for idx, snippet in sorted(inserts, key=lambda x: x[0], reverse=True):
        body = body[:idx] + snippet + body[idx:]
    return body


def _needs_alignment(text: str, enforce_name: str | None, allowed_names: list[str] | None = None, disallowed: list[str] | None = None) -> bool:
    if not text:
        return True
    if enforce_name and enforce_name not in text:
        return True
    # detect unwanted mentions
    banned_tokens = (disallowed or [])
    allowed = set((allowed_names or []))
    if enforce_name:
        allowed.add(enforce_name)
    for t in banned_tokens:
        if t in text and not any(a and a in t or t in a for a in allowed):
            return True
    return False


async def generate_post_markdown(keyword: str, candidate: ProductCandidate, affiliate_url: str, affiliate_html: str | None = None, template_type: str = "A", template_input: dict | None = None):
    # provider resolved in ai_client
    template_id = random.choice(["A", "B", "C"])

    data = {
        "keyword": keyword,
        "product_name": f"{candidate.brand or ''} {candidate.model or ''}".strip() or candidate.title_guess,
        "price_band": candidate.price_band or '',
        "affiliate_url": affiliate_url,
    }
    if template_input:
        data.update(template_input)
    user = build_user_prompt(template_type, data)

    try:
        text, total_tokens = await complete_chat(
            messages=[
                {"role": "system", "content": WRITER_SYSTEM},
                {"role": "user", "content": user},
            ],
            temperature=0.8,
            max_tokens=2000,
            purpose='writer',
        )
    except Exception as e:
        msg = str(e)
        if 'not configured' in msg:
            raise AIError("config_error", msg)
        if 'policy_block' in msg or 'blocked' in msg:
            raise AIError("policy_block", msg)
        raise AIError("network_error", f"AI API request failed: {e}")
    content = text
    if not content:
        raise AIError("empty_response", "OpenAI returned empty content for post writer")
    total_tokens = total_tokens or 800
    async with AsyncSessionLocal() as session:
        await add_usage(session, total_tokens)
    # enforce disclosure + link once
    content = _ensure_disclosure_and_link(content, affiliate_url)
    # alignment guard: ensure correct product appears, and unrelated tokens removed
    enforce_name = (template_input or {}).get('enforce_product_name') if template_input else None
    allowed_names = (template_input or {}).get('allowed_names') if template_input else None
    disallowed = (template_input or {}).get('disallowed_brands') if template_input else None
    if _needs_alignment(content, enforce_name, allowed_names, disallowed):
        rev_user = (
            "다음 글을 제약에 맞게 자연스럽게 재작성하세요.\n"
            + (f"반드시 '{enforce_name}' 제품명을 사용하고, 목록 외 다른 모델명은 언급하지 말 것.\n" if enforce_name else "")
            + (f"허용된 모델명: {allowed_names}. 이 외 모델/브랜드는 삭제.\n" if allowed_names else "")
            + (f"금지 키워드(브랜드/모델): {disallowed}. 본문에서 제거.\n" if disallowed else "")
            + "링크 위치(서두/표 아래/결론부)는 유지. 문장 길이 다양화, 동의어 치환으로 더 사람스럽게.\n\n"
            + content
        )
        try:
            new_text, more_tokens = await complete_chat(
                messages=[
                    {"role": "system", "content": WRITER_SYSTEM},
                    {"role": "user", "content": rev_user},
                ],
                temperature=0.7,
                max_tokens=2000,
                purpose='writer',
            )
            if new_text:
                content = _ensure_disclosure_and_link(new_text, affiliate_url)
                total_tokens = (total_tokens or 0) + (more_tokens or 0)
        except Exception:
            pass
    # title extraction
    lines = content.splitlines()
    title = next((l.replace("#", "").strip() for l in lines if l.strip().startswith("# ")), f"[광고/제휴] {keyword} 리뷰")
    tags = [keyword.replace(" ", ""), "쿠팡파트너스"]
    images = ["제품 패키지 사진", "사용 상황 사진"]
    # inject affiliate iframe HTML at the end if provided and not already present
    if affiliate_html and (affiliate_html not in content):
        content = content.rstrip() + "\n\n" + affiliate_html + "\n"
    return content, title, tags, images, template_id
