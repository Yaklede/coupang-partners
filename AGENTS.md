# AGENTS.md — 쿠팡파트너스 네이버블로그 자동 포스팅 시스템

> 목표: 하루 10~100개 포스트까지 확장 가능한 **자동·반자동 포스팅 파이프라인** 구축. 네이버 DataLab→키워드→상품 추천→제휴링크 매핑→사람처럼 보이는 글 자동 생성·게시. **월 OpenAI 비용 20달러 이하** 유지.

---

## 0) 시스템 한눈에 보기

* **유형**: 에이전트 오케스트레이션 + 휴먼 인더 루프(HITL)
* **주요 제약**:

    * (중요) *쿠팡 파트너스 API 미사용*. 필요 데이터는 **웹 스크래핑** 또는 수동 업로드/CSV로 대체.
    * 네이버 블로그 게시: **Naver Developers API** 사용 (OAuth2, 일일/분당 레이트 고려).
    * **AI 글 티 안 나게**: 인적 필치 규칙 + 사실 근거 + 템플릿 랜덤화 + 미세 노이즈(개인적 관찰·체크리스트) 삽입.
    * **예산 가드**: 토큰/요청 수를 중앙에서 상한 관리.

---

## 1) 아키텍처

* **Orchestrator**: 전반 플로우 관리(State Machine)
* **KeywordAgent**: 네이버 DataLab에서 인기 키워드 수집·필터·클러스터링
* **ProductScoutAgent**: 키워드→상품 후보 추천(OpenAI) + 중복/재등록 방지
* **MappingUI (HITL)**: 후보 리스트 렌더링, **사용자 제휴링크 매핑**
* **PostWriterAgent**: 사람 필치로 본문/제목/요약/CTA 생성, 이미지 제안
* **SEOAgent**: 메타 키워드, 태그, 내부링크/아웃링크 제안
* **Publisher**: 네이버 블로그 API 게시/예약
* **BudgetGuardian**: 토큰/호출 카운팅, 모델 스위칭(저가↔고품질)
* **Logger & Reviewer**: 수익/CTR/노출 로그 적재, A/B 템플릿 실험

```
[DataLab]→KeywordAgent→ProductScoutAgent→(HITL: 링크 매핑)→PostWriterAgent→SEOAgent→Publisher→Logger
                                           ↑                                             ↓
                                      BudgetGuardian <——————————————— Metrics/ROI ——————————→
```

---

## 2) 엔드투엔드 플로우(상세)

1. **키워드 수집**

    * DataLab(쇼핑인사이트/검색어 트렌드)에서 최근 1~7일 상위 키워드 수집
    * 불용어/금칙어 필터, 상업성·계절성 스코어링, 카테고리 라벨링
2. **상품 후보 추천(OpenAI)**

    * 키워드별 **쿠팡 내 유력 상품을 추론** (제조사/브랜드/모델 패턴, 리뷰량/가격대 범주 등 규칙 기반 + LLM 보강)
    * 이미 **등록한 상품/포스트 중복 방지** (DB 조회)
    * 출력: `[{keyword, title_guess, brand, model, price_band, why, image_hint}]`
3. **HITL: 제휴링크 매핑**

    * UI에서 후보 리스트를 **한 눈에 정렬/검색**
    * 사용자: 각 항목에 **쿠팡 파트너스 제휴링크** 붙이기(수동/붙여넣기)
    * 완료 상태만 다음 단계로 진입
4. **사람처럼 보이는 글 자동작성**

    * 템플릿 A/B/C + 랜덤화(문장 길이, 조사 변주, 개인적 관찰/체크리스트/사용팁) + **팩트 기반 근거**(상품페이지/리뷰에서 요약한 사실) 삽입
    * **과장·허위·의학적 주장 금지**, 광고 표시 문구 포함(예: “본 포스트에는 제휴 링크가 포함됩니다.”)
    * 이미지: 원문 저작권 준수(직접 캡처 지양, 퍼블릭 도메인/제조사 보도자료 허용 범위 확인)
5. **SEO·형식화**

    * 제목 2안 이상 생성(숏·롱), H1~H3, 목차, FAQ(구글·네이버 PAA 스타일 질문), 요약 TL;DR, 해시태그
    * 내부링크(내 포스트) / 아웃링크(공신력 출처) 추천
6. **게시/예약**

    * 네이버 블로그 API로 즉시 게시 or 예약(시간대 분산)
    * 실패 시 재시도 백오프, 초과 실패는 큐 보류 + 슬랙 알림
7. **로그/메트릭**

    * 포스트 ID, 키워드, 클릭/전환(가능한 범위) 적재
    * 다음 라운드에 CTR 낮은 템플릿 가중치 하향

---

## 3) 데이터 모델(요약)

* `keyword(id, text, date_range, score, category, status)`
* `product_candidate(id, keyword_id, title_guess, brand, model, price_band, why, image_hint, dedupe_key, status)`
* `affiliate_map(id, product_candidate_id, affiliate_url, mapped_by, mapped_at)`
* `post(id, keyword_id, product_candidate_id, title, body_md, tags, images, status, published_at, naver_post_id)`
* `metrics(post_id, impressions?, clicks?, ctr?, revenue?, template_id)`
* `budget(date, token_used, usd_spent, cap=20)`

---

## 4) 환경설정 예시

```yaml
openai:
  model_small: gpt-small      # 키워드/상품 스카우트(저가)
  model_writer: gpt-medium    # 글/SEO(품질)
  max_usd_month: 20
  hard_stop: true             # 초과 예상 시 자동 중단

naver:
  blog_api_client_id: ${NAVER_CLIENT_ID}
  blog_api_client_secret: ${NAVER_CLIENT_SECRET}
  blog_id: ${NAVER_BLOG_ID}
  rate_limit_per_min: 10

pipeline:
  posts_per_day_min: 10
  posts_per_day_max: 100
  posting_window: [09:00, 23:30]  # 분산 예약
  allow_manual_review: true
  language: ko-KR

templates:
  rotate: [A, B, C]
  avoid_ai_markers: true
  include_disclosure: true
```

---

## 5) 프롬프트 설계(복붙용)

### (A) ProductScoutAgent — 상품 후보 추천

**System**

```
당신은 이커머스 MD입니다. 사용자가 준 검색어(네이버 이용자 관점)와 쇼핑 의도를 바탕으로, 쿠팡에서 잘 팔릴 법한 상품 후보를 5~12개 제안하세요.
출력은 JSON 배열. 각 항목은 {"title_guess","brand","model","price_band","why","image_hint"}를 포함.
이미 판매 종결/단종/사기성 제품은 제외. 동일 모델 변형은 1~2개만.
```

**User**

```
키워드: "${keyword}"
내가 이미 올린 상품 dedupe 키 목록: ${dedupe_keys}
가격대 범위: ${price_pref}
```

**Notes**

* 토큰 절약 위해 `max_tokens` 낮게, `temperature` 0.3.

### (B) PostWriterAgent — 사람 필치 글 생성

**System**

```
당신은 네이버 블로그 체질의 생활형 리뷰어입니다. AI 티가 나지 않게, 한국어 구어체+경험담+체크리스트를 섞어 씁니다.
규칙:
- 문장 길이와 조사를 랜덤 변주(너무 규칙적 X)
- 사실 근거는 상품 상세 요약 범위에서만(허위·의학적 주장 금지)
- 상업성 노출은 솔직하게: "*본 포스트에는 제휴 링크가 포함됩니다*" 포함
- 섹션 구성: 인트로(상황 공감)→핵심 포인트 3~5→사용 팁/주의→누구에게 맞는지→간단 요약→FAQ 2~4개
- 제목 2안(짧게/길게) + 해시태그 8~12개 + TL;DR 2문장
- 마크다운으로 출력. 링크 자리는 ${affiliate_url} 플레이스홀더 사용
- 이미지 제안(캡션만): 2~3개
```

**User**

```
키워드: ${keyword}
상품 요약(사실): ${factual_bullets}
내 관찰(선택): ${personal_notes}
제휴링크: ${affiliate_url}
지양하는 표현: 인공지능, 생성형, 거짓 과장
```

### (C) SEOAgent — 메타/태그

**System**

```
블로그 SEO 어시스턴트. 네이버 검색에 맞게 제목/소제목 키워드 매핑, 태그, 내부/외부 링크 후보를 제안.
출력: {"title_short","title_long","h2","h3","tags":[..],"internal_link_suggestions":[..],"external_link_suggestions":[..]}
```

**User**

```
본문 마크다운: <paste>
내 포스트 인덱스: ${my_posts_index_titles_urls}
```

---

## 6) 사람 필치(안티 AI-톤) 가이드

* **개인 맥락 한 스푼**: “이번 추석에 부모님 선물로 알아보다가…” 같은 짧은 배경 1~2문장
* **구체적 사용 팁**: 수치/사이즈/공간 제약/소음 등 생활형 디테일
* **주관적 체감**: 장점 70 / 단점 30 비율로, 단점도 솔직히 기술
* **문장 리듬**: 6~18자 짧은 문장과 30~60자 긴 문장을 섞기
* **불필요한 영문·이모지 과다 금지**, 느낌표 남용 금지
* **광고 고지** 포함(법규 준수)

---

## 7) 네이버 API/레이트/예약 전략(개요)

* OAuth2 토큰 캐시 + 자동 리프레시
* 분당/일일 호출 상한 근사치 설정 후 **토큰 버킷**
* 게시 **예약 분산**(예: 09:00~23:30 사이 12~22분 간격 랜덤)
* 실패: 지수 백오프(10s, 30s, 2m, 5m), 5회 초과 시 슬랙 알림+보류 큐

---

## 8) 예산 가드(월 $20)

* **예상비용=Σ(요청수×평균토큰×단가)**
* 일일 한도=`20/30≈$0.66`. 오케스트레이터가 **일일 토큰/요청 상한** 자동 계산
* 단계별 모델 스위칭:

    * Keyword/Product: 소형 모델
    * Writer/SEO: 중형 모델, 단 **포스트 수가 많은 날** 소형으로 강등
* 토큰 절약 테크닉:

    * 프롬프트/컨텍스트 최소화, 상품 사실요약은 자체 요약 캐시 사용
    * 제목/FAQ 1~2안으로 제한, 실패 시 재생성 금지

---

## 9) 품질 체크리스트(출시 전/배포 전)

* [ ] 광고 고지 문구 포함
* [ ] 허위·과장·의학적/법률적 주장 없음
* [ ] 문장 길이·조사 변주 OK, 반복 패턴 없음
* [ ] 이미지 저작권 출처 확인
* [ ] 제휴링크 정상 리다이렉트 확인
* [ ] 키워드 매칭(제목/H2/H3/태그) 점검
* [ ] 예약 시간 분산 적용
* [ ] 로그/메트릭 수집 정상

---

## 10) 오류 처리 & 재시도 정책

* **DataLab 실패**: 캐시된 과거 3~7일 키워드 사용 → 알림
* **상품 추천 실패**: 로컬 규칙 기반 백업(브랜드 사전+가격대 사전)
* **네이버 게시 실패**: 5회 백오프 후 큐 보류, 수동 재시도 버튼 제공
* **토큰 초과 예상**: 당일 파이프라인 자동 중단 + 다음날 재개

---

## 11) 의존 서비스 & 보안

* 비밀키(.env): OpenAI, NAVER_CLIENT_ID/SECRET, Slack Webhook
* 네트워크: 요청 서명/리퍼러 제어(가능시)
* 로그: PII 저장 금지, 포스트 본문은 DB 암호화 옵션

---

## 12) 간단 API 스펙(내부)

* `POST /keywords/fetch` → DataLab 크롤/집계 실행
* `POST /products/recommend` {keyword_id} → 후보 생성
* `GET /products?status=pending` → 매핑 UI 데이터
* `POST /affiliate/map` {product_id, url}
* `POST /posts/draft` {product_id} → 초안 생성
* `POST /posts/publish` {post_id, schedule?}
* `GET /metrics/posts` {from,to}

---

## 13) 템플릿 예시(요약)

**제목 패턴**

* 숏: "${키워드} 이거 사봤더니, 핵심만"
* 롱: "${키워드} 후기: 쓰면서 느낀 장단점·주의할 점 총정리"

**본문 마크다운 스캐폴드**

```
# ${title}
> *본 포스트에는 제휴 링크가 포함됩니다.*

오늘은 ${keyword}를 실제로 써보면서 느낀 점을 간단히 정리해둡니다. (…개인 맥락 1~2문장…)

## 핵심 한 줄 요약
- ${tldr1}
- ${tldr2}

## 왜 이 제품?
- ${reason_bullets}

## 써보니 좋았던 점
1. …
2. …

## 아쉬운 점(솔직하게)
- …

## 이런 분께 추천
- …

## 사용 팁/주의
- …

[자세히 보기](${affiliate_url})

---
### FAQ
- Q: …  A: …
- Q: …  A: …

### 해시태그
#${tag1} #${tag2} …
```

---

## 14) 운영 전략

* **초기(1~2주)**: 품질 우선(하루 10~20개), 템플릿·톤 튜닝
* **확장(3주~)**: 30~60개/일, 예약 분산, 내부링크 네트워크 구축
* **안정화**: CTR·전환 기반 템플릿 가중치 자동 조정, 저품질 키워드 자동 배제

---

## 15) TODO

* [ ] DataLab 크롤러 구현(프록시/우회 대비)
* [ ] 상품 사실요약 캐시 스키마
* [ ] 네이버 OAuth2 플로우 & 토큰 캐시
* [ ] 슬랙 알림(오류/예산/완료)
* [ ] 대시보드(오늘 포스트/예산/CTR)
* [ ] A/B 템플릿 실험 파이프라인
