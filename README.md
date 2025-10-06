## Coupang Partners Automation (Miner Skeleton)

This repo implements a dual-mode Coupang product miner selectable between `crawler` and `api`. Default mode is `crawler` since API keys may be unavailable.

### Quickstart

1) Create and edit `config.yaml` from the example:

```
cp config.example.yaml config.yaml
cp .env.example .env
```

2) Install dependencies (Python 3.10+) — optional if using Docker:

```
pip install -r requirements.txt
```

3) Run a search (crawler mode by default):

```
python -m coupang_partners.cli search "가습기" --limit 5
```

4) Force API mode (requires keys in env):

```
python -m coupang_partners.cli search "가습기" --mode api
```

### Configuration

`config.yaml` includes a `coupang_source.mode` key:

```
coupang_source:
  mode: crawler  # crawler | api | auto
```

When set to `auto`, the miner uses API if `COUPANG_OPENAPI_ACCESS_KEY` and `COUPANG_OPENAPI_SECRET_KEY` are present, otherwise falls back to the crawler.
For affiliate links, see `affiliate` section below.

### Notes

- The API miner is a minimal skeleton and may require adjusting endpoints/auth per Coupang Partners Open API documentation.
- The crawler is best-effort HTML parsing and may break if site markup changes. Use responsibly and respect robots.txt and site policies.

## Docker Usage

Build image:

```
docker build -t coupang-partners:local .
```

Run with Docker (mount config and env):

``
docker run --rm \
  --env-file .env \
  -v "$PWD/config.yaml":/app/config.yaml \
  coupang-partners:local search "가습기" --limit 5
``

Or with Docker Compose:

```
docker compose build
docker compose run --rm app search "가습기" --limit 5
```

### Web GUI

Run the GUI server (FastAPI) and open http://localhost:8000:

```
docker compose up -d web
# then visit http://localhost:8000
```

From the GUI you can:
- Set run count, select coupang source mode, toggle dry-run
- Trigger the full pipeline; see JSON results inline
Future: config editing, logs, history, and scheduling can be added.

### Connect Naver (OAuth) in GUI

1) Open `http://localhost:8000` → "네이버 연결(OAuth)" 카드에서 Client ID/Secret/Redirect URI 입력 후 "자격증명 저장".
2) Naver Developers 콘솔에도 동일한 Redirect URI 등록: `http://localhost:8000/oauth/naver/callback`.
3) "네이버 연결" 클릭 → 로그인/동의 후 액세스 토큰이 로컬 `secrets/naver_token.json`에 저장됩니다.
4) 이후 파이프라인 실행 시 자동으로 해당 토큰을 사용해 블로그 게시합니다.

Notes: 이 토큰/자격증명은 로컬 파일에 저장되며, 저장소 커밋을 피하기 위해 `secrets/`는 `.gitignore` 처리되어 있습니다.

### OpenAI Base URL 설정

- 기본(OpenAI 공식 API): 별도 설정 없이 `.env`에 `OPENAI_API_KEY`만 있으면 됩니다. SDK 기본 Base URL은 `https://api.openai.com/v1` 입니다.
- 프록시/게이트웨이/자체 엔드포인트 사용: `.env`에 `OPENAI_BASE_URL`을 해당 엔드포인트로 지정하세요(예: `https://my-gateway.example.com/v1`).
- Azure OpenAI를 사용할 경우에는 Azure 전용 엔드포인트와 배포 모델 구성을 따라야 하며, 본 리포지토리의 기본 예제는 표준 OpenAI API 엔드포인트를 가정합니다.

### Coupang Partners 링크 생성

- 설정: `config.yaml`의 `affiliate` 섹션

```
affiliate:
  generation: none            # none | partners_api | portal (beta)
  require_for_publish: true   # true면 제휴링크 없으면 게시 스킵
```

- 권장: `partners_api` (공식 Partners Open API 필요) — 현재 코드는 자리표시이며, 실제 딥링크 변환 엔드포인트 연동이 필요합니다.
- `portal`(beta): 포털 로그인 자동화는 보안/정책/2FA 이슈로 기본 비활성화(자리표시). 정책 위반 위험이 있으므로 추천하지 않습니다.
- `none`: 제휴링크를 만들지 않음. `require_for_publish: true`인 경우 게시를 스킵합니다.


Force API mode (keys required in `.env` or `-e`):

```
docker compose run --rm app search "가습기" --mode api
```

Enrich a single product JSON:

```
docker compose run --rm app enrich '{"id":"123","title":"test","url":"https://www.coupang.com/..."}'
```

### Full Pipeline (Auto)

Runs: keyword extraction (OpenAI) → Coupang mining → LLM write/refine/SEO → Naver blog post.

```
docker compose run --rm app run --count 2
```

Configuration used:

- OpenAI model: `providers.openai.model` (from `config.yaml`)
- Keywords: `keywords.daily_count`, plus optional seed categories
- Coupang source: `coupang_source.mode` (default `crawler`)
- Naver: requires `NAVER_ACCESS_TOKEN` in `.env`
- Affiliate links: set `affiliate.generation` (default `none`). When `require_for_publish: true`, posts are skipped until a valid affiliate link is available.

Outputs a JSON summary and posts to Naver when token is present. Without a token, it will skip publishing and mark the status as `skipped`.
