% Full Pipeline (Auto)

This pipeline runs without manual keyword input:

- Keyword extraction (OpenAI)
- Coupang mining (crawler/api selectable; default crawler)
- LLM writing (Writer → Refiner → SEO)
- Naver Blog publish

## Run

```
docker compose run --rm app run --count 2
```

- `--count` defaults to `app.target_posts_per_day` in `config.yaml`.
- Output is printed as JSON and optionally saved with `--output results.json`.

## Configuration

- `providers.openai.model`: LLM model for all stages
- `keywords.*`: daily count, seed categories, fallback list
- `coupang_source.mode`: `crawler | api | auto`
- `posting.mode`: `draft | public` (Naver API may not support drafts explicitly)
- `posting.default_category_no`, `posting.hashtags`

## Environment

- `.env` must contain `OPENAI_API_KEY`
- Optional Coupang API keys enable API mode automatically (`auto`)
- Naver publishing requires `NAVER_ACCESS_TOKEN` (OAuth token)

## Notes

- Crawler selectors can break if the site markup changes; prefer API mode when keys are available.
- The Writer/Refiner/SEO prompts are embedded per AGENTS.md guidance to reduce “AI-like” tone.
- The final HTML appends the mandatory disclosure required for affiliate links.

