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

Outputs a JSON summary and posts to Naver when token is present. Without a token, it will skip publishing and mark the status as `skipped`.
