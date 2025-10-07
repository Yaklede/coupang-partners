WRITER_SYSTEM = (
    "역할: 당신은 네이버/티스토리 스타일의 생활형 리뷰 블로거입니다. 자연스러운 1인칭 경험담 톤으로, 과장 없이 근거를 제시합니다. 최근 상위 노출 글들의 작성 패턴(상단 요약, 중간 CTA, 비교표, 결론 직전 링크, 내부/외부 링크)을 따릅니다.\n"
    "핵심 규칙:\n"
    "- 출력은 마크다운 '완성 글'만. 메타 라벨(예: '제목 1/2', 'Intro', 'TL;DR', 'FAQ', '체크리스트') 금지.\n"
    "- 첫 줄은 '# 제목', 둘째 줄은 광고 고지 문구 한 줄: '*본 글은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.*'\n"
    "- 서두: 3줄 요약(누가/왜/결론)을 첫 1~2문단 내에 자연스럽게 배치.\n"
    "- 본문은 8~14개 문단, H2 소제목 3~5개(예: '써보니 좋았던 점', '아쉬웠던 부분', '사용 팁', '이런 분께 추천').\n"
    "- 링크 배치(CTA 2~3회, 과도한 반복 금지): (1) 서두 요약 직후 짧은 텍스트 링크, (2) 비교표 아래 1회, (3) 결론 시작 문장에 자연 유도 링크. 앵커 문구는 매번 다르게(예: '자세히 보기'/'상세 스펙·최저가 확인'/'지금 재고 확인'). 링크는 모두 ${affiliate_url} 사용.\n"
    "- 해시태그 8~12개를 글 맨 끝 한 줄로 배치(#키워드 형식).\n"
    "- 사실은 상품 상세/리뷰/제조사 공식문서 범위 내에서만. 임의 수치·의학·법률 주장 금지. 비교군 1개 이상 언급.\n"
    "- 길이: 최소 1,600자 이상. 문장 길이 다양화, 동의어 치환으로 AI 티 제거.\n"
    "- 'spec_table_md'가 제공되면 본문 상단 1/3 지점에 표를 그대로 포함. 'sources'가 있으면 문말에 '참고 링크'로 2~4개 나열.\n"
    "- 이미지: 캡션 1문장과 ALT 문구를 함께 제시(한국어), 본문 맥락과 연결.\n"
    "- 내부/외부 링크: 본문 중간에 내 글 1개(연관)와 공식문서 1개를 자연스러운 문장으로 제시(실제로는 편집 시 연결하니 앵커 문장만 작성).\n"
)


def build_user_prompt(template_type: str, data: dict) -> str:
    """Create user prompt based on template types A~E from user's guide.
    data keys vary by template. Accepts:
      common: keyword, product_name, price_band, affiliate_url
      A: period, place, measures, comparisons, reader_points, photo_keywords
      B: category, items(list), scenario_keywords
      C: theme, items(list)
      D: problem, stages(list)
      E: event, picks(list)
    """
    t = (template_type or "A").upper()
    # Common fallbacks
    keyword = data.get("keyword", "")
    product_name = data.get("product_name", "")
    price_band = data.get("price_band", "")
    affiliate_url = data.get("affiliate_url", "")

    if t == "A":
        return (
            "카테고리: 실사용 리뷰형(단일 제품)\n"
            f"제품명: {product_name}\n"
            f"핵심키워드: {keyword}\n"
            f"가격대: {price_band}\n"
            f"사용 기간/장소/활동: {data.get('period','2주')}, {data.get('place','집')}, {data.get('activity','일상 청소')}\n"
            f"측정 항목/수치: {data.get('measures','소음, 사용시간 등 체감 위주')}\n"
            f"비교 대상: {data.get('comparisons','동급 타사 1~2개')}\n"
            f"독자 궁금 포인트: {data.get('reader_points','소음/보관/가성비')}\n"
            f"사진 설명 키워드: {data.get('photo_keywords','사용 장면, 보관, 구성품')}\n"
            f"링크 플레이스홀더: {affiliate_url}\n"
            + (f"권장 스펙 축: {', '.join(data.get('spec_keys', []))}\n" if data.get('spec_keys') else "")
+ "제약: 제목은 '[광고/제휴] '로 시작. 서두 3~5문장, 한줄 총평 포함. 본문 섹션에 장/단점 균형과 대안 제시 포함.\n"
            + ("\n제공 표(spec_table_md):\n" + data.get('spec_table_md') + "\n" if data.get('spec_table_md') else "")
            + ("\n참고 링크(sources):\n- " + "\n- ".join(data.get('sources', [])) + "\n" if data.get('sources') else "")
            + "출력: 마크다운 완성 글. 첫 줄 제목, 둘째 줄 광고 고지, 이후 본문과 해시태그.\n"
        )
    elif t == "B":
        return (
            "카테고리: 비교 가이드형(2~4개)\n"
            f"카테고리명: {data.get('category', keyword)}\n"
            f"후보: {data.get('items','[]')}\n"
            f"사용시나리오 키워드: {data.get('scenario','가성비/조용함/내구')}\n"
            f"링크 플레이스홀더: {affiliate_url}\n"
            + (f"권장 비교 축: {', '.join(data.get('spec_keys', []))}\n" if data.get('spec_keys') else "")
            + ("\n비교 표(spec_table_md):\n" + data.get('spec_table_md') + "\n" if data.get('spec_table_md') else "")
            + ("\n참고 링크(sources):\n- " + "\n- ".join(data.get('sources', [])) + "\n" if data.get('sources') else "")
            + "제약: 표 1개(핵심지표 6~8, 제공된 spec_table_md가 있으면 그대로 사용), 시나리오별 추천, 장단점 요약, 구매 전 체크포인트.\n"
            + "출력: 마크다운 완성 글(제목/고지/본문/해시태그).\n"
        )
    elif t == "C":
        return (
            "카테고리: 리스트·큐레이션형(5~9개)\n"
            f"테마: {data.get('theme', keyword)}\n"
            f"아이템들: {data.get('items','[]')}\n"
            f"링크 플레이스홀더: {affiliate_url}\n"
            "제약: 아이템 카드 반복(적합 대상/핵심 포인트/사용 장면/주의). 마무리 선택 가이드.\n"
            "출력: 마크다운 완성 글(제목/고지/본문/해시태그).\n"
        )
    elif t == "D":
        return (
            "카테고리: 문제 해결형(튜토리얼+추천)\n"
            f"문제/증상: {data.get('problem', keyword)}\n"
            f"단계: {data.get('stages','3~5단계로 제시')}\n"
            f"링크 플레이스홀더: {affiliate_url}\n"
            "제약: 단계별 성공 기준/실패 시 다음 단계, 각 단계 도구 1~2개. 안전/보증 유의 3줄.\n"
            "출력: 마크다운 완성 글(제목/고지/본문/해시태그).\n"
        )
    elif t == "E":
        return (
            "카테고리: 시즌/행사 특가형\n"
            f"행사/시즌: {data.get('event', keyword)}\n"
            f"Top Picks: {data.get('picks','3개 제시')}\n"
            f"링크 플레이스홀더: {affiliate_url}\n"
            "제약: 기간/변동성/환불 체크, 카테고리별 Top Pick 3개(이유/리스크), 가격 신호 3개, 알림 유도.\n"
            "출력: 마크다운 완성 글(제목/고지/본문/해시태그).\n"
        )
    else:
        return (
            f"카테고리: 기타({t})\n"
            f"키워드: {keyword}\n"
            f"링크 플레이스홀더: {affiliate_url}\n"
            "출력: 마크다운 완성 글 규칙을 따를 것.\n"
        )
