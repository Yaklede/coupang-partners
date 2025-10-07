from urllib.parse import quote_plus


def build_coupang_search_url(title_guess: str | None = None, brand: str | None = None, model: str | None = None, keyword: str | None = None) -> str:
    query_parts = []
    for s in [brand, model]:
        if s:
            query_parts.append(str(s))
    base = ' '.join(query_parts).strip()
    if not base:
        base = (title_guess or keyword or '').strip()
    q = quote_plus(base)
    return f"https://www.coupang.com/np/search?q={q}&channel=user"

