from __future__ import annotations
import re
from typing import Dict, List, Optional
import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


async def fetch_coupang_product_specs(url: str, timeout: float = 15.0) -> Dict:
    """Scrape basic specs from a Coupang product page. Best-effort parser.
    Returns dict with title, price_text, bullets(list), specs(dict), images(list), source_url.
    """
    if not url:
        return {}
    async with httpx.AsyncClient(headers=HEADERS, timeout=timeout, follow_redirects=True) as client:
        r = await client.get(url)
    if r.status_code != 200:
        return {"source_url": url}
    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    title = (soup.select_one('h2.prod-buy-header__title') or soup.select_one('#productTitle') or soup.find('title'))
    title_text = title.get_text(strip=True) if title else ''
    price_el = soup.select_one('.total-price') or soup.select_one('.prod-sale-price')
    price_text = price_el.get_text(" ", strip=True) if price_el else ''
    # bullets
    bullets = []
    for li in soup.select('.prod-description-attribute li, .prod-attr-list li, .prod-feature li')[:12]:
        bullets.append(li.get_text(" ", strip=True))
    # specs table
    specs: Dict[str, str] = {}
    for row in soup.select('.prod-description-table tr, table tr'):
        th = row.find('th')
        td = row.find('td')
        if th and td:
            key = th.get_text(" ", strip=True)
            val = td.get_text(" ", strip=True)
            if key and val and len(key) < 40 and len(val) < 200:
                specs[key] = val
    images = []
    for img in soup.select('.prod-image__detail img, .prod-image__items img, img[src]')[:8]:
        src = img.get('data-src') or img.get('src')
        if src and src.startswith('http'):
            images.append(src)
    return {
        "title": title_text,
        "price_text": price_text,
        "bullets": bullets,
        "specs": specs,
        "images": images,
        "source_url": str(r.url),
    }


def build_spec_table(products: List[Dict], columns: Optional[List[str]] = None) -> str:
    """Build a markdown comparison table given a list of product spec dicts.
    Each product dict expects: name, specs(dict with normalized keys like 용량, 소음(dB), 전력(W), 무게(kg)), price_text.
    """
    # Choose default columns if not provided
    default_cols = ["용량", "소음(dB)", "전력(W)", "무게(kg)", "특징"]
    cols = columns or default_cols
    header = "| 모델 | " + " | ".join(cols) + " |\n"
    sep = "|---" * (len(cols) + 1) + "|\n"
    rows = []
    for p in products:
        name = p.get('name') or p.get('title') or ''
        specmap = p.get('specs', {})
        values = []
        for c in cols:
            v = specmap.get(c)
            if not v and c == "특징":
                v = p.get('feature') or ''
            values.append(v or '')
        rows.append("| " + name + " | " + " | ".join(values) + " |\n")
    return header + sep + "".join(rows)

