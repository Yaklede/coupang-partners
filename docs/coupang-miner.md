# Coupang Miner (Dual-Mode)

Implements two interchangeable backends for product discovery:

- `crawler`: Scrapes Coupang search and product pages (default)
- `api`: Uses Coupang Partners Open API (requires keys)

## Select Backend

`config.yaml`:

```
coupang_source:
  mode: crawler  # crawler | api | auto
```

- `crawler`: always use HTML crawler
- `api`: always use Open API
- `auto`: use API when both `COUPANG_OPENAPI_ACCESS_KEY` and `COUPANG_OPENAPI_SECRET_KEY` are present; otherwise fallback to crawler.

You can also override per-run with CLI `--mode`.

## Environment Variables

```
COUPANG_PARTNER_ID=        # optional; appended as query param to deeplinks
COUPANG_OPENAPI_ACCESS_KEY # required for api mode
COUPANG_OPENAPI_SECRET_KEY # required for api mode
```

## CLI Usage

```
python -m coupang_partners.cli search "키워드" --limit 5
python -m coupang_partners.cli search "키워드" --mode api
```

Output is a JSON `ProductSearchResult` with `items[]` of `Product`.

To enrich a single product (fetch details/images when available):

```
python -m coupang_partners.cli enrich '{"id":"...","title":"...","url":"https://www.coupang.com/..."}'
```

## Implementation Notes

- Crawler selectors target `li.search-product > a.search-product-link` etc. Markup can change; treat as best-effort.
- API miner includes a generic HMAC header generator but the endpoint path may require adjustment per official docs.
- Deeplink construction follows AGENTS.md Annex B: `?src=blog&partner=...&keyword=...` appended to product URL.

## Compliance & Hygiene

- Respect robots.txt and site policies. Use reasonable delays (the crawler adds a small randomized delay).
- Avoid high-frequency scraping. Prefer the official API when available.

