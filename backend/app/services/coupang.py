from __future__ import annotations
import re
from urllib.parse import quote_plus
from typing import Optional
import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def search_url(query: str) -> str:
    return f"https://www.coupang.com/np/search?q={quote_plus(query)}&channel=user"


async def fetch_top_product_url(query: str, timeout: float = 12.0) -> Optional[str]:
    """Return first product page URL from Coupang search results or None if not found.
    Non-auth scraping; best-effort.
    """
    url = search_url(query)
    async with httpx.AsyncClient(headers=HEADERS, timeout=timeout, follow_redirects=True) as client:
        r = await client.get(url)
    if r.status_code != 200:
        return None
    html = r.text
    # Common pattern: /vp/products/<id>
    m = re.search(r"/vp/products/(\d+)", html)
    if m:
        pid = m.group(1)
        return f"https://www.coupang.com/vp/products/{pid}"
    # Fallback to parsing anchors
    soup = BeautifulSoup(html, 'html.parser')
    a = soup.select_one('a.search-product-link') or soup.select_one('a[href*="/vp/products/"]')
    if a and a.get('href'):
        href = a['href']
        if href.startswith('http'):  # sometimes absolute
            return href
        return f"https://www.coupang.com{href}"
    return None

