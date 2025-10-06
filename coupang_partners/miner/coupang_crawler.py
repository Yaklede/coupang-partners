from __future__ import annotations

import os
import re
import urllib.parse
from typing import List

from bs4 import BeautifulSoup

from ..models import Product
from ..utils.http import get


SEARCH_URL = "https://www.coupang.com/np/search"


class CoupangCrawlerMiner:
    def __init__(self, partner_id: str | None = None):
        self.partner_id = partner_id or os.getenv("COUPANG_PARTNER_ID")

    def _build_deeplink(self, url: str, keyword: str) -> str:
        # IMPORTANT: Official Coupang Partners affiliate links are generated
        # via the Partners portal or the Partners Open API after authentication.
        # Building a link by adding arbitrary query params is NOT guaranteed to
        # track correctly and may violate policy.
        # In crawler mode without API/portal automation, return the raw URL and
        # let the orchestrator attempt affiliate conversion later.
        return url

    def search_products(self, keyword: str, limit: int = 10) -> List[Product]:
        q = urllib.parse.quote(keyword)
        url = f"{SEARCH_URL}?q={q}&channel=user"
        resp = get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        items: List[Product] = []
        for li in soup.select("li.search-product"):
            if len(items) >= limit:
                break

            # Skip ads (usually have class 'search-product__ad-badge')
            if li.select_one(".search-product__ad-badge"):
                continue

            a = li.select_one("a.search-product-link")
            if not a:
                continue
            href = a.get("href")
            if not href:
                continue
            product_url = urllib.parse.urljoin("https://www.coupang.com", href)

            title_el = li.select_one(".name")
            price_el = li.select_one(".price-value")
            rating_el = li.select_one(".star")
            review_cnt_el = li.select_one(".rating-total-count")

            title = title_el.get_text(strip=True) if title_el else ""
            price = None
            if price_el and price_el.text:
                try:
                    price = float(re.sub(r"[^0-9]", "", price_el.text))
                except Exception:
                    price = None

            rating = None
            if rating_el and rating_el.get("data-rating"):
                try:
                    rating = float(rating_el.get("data-rating"))
                except Exception:
                    rating = None

            review_cnt = None
            if review_cnt_el and review_cnt_el.text:
                try:
                    review_cnt = int(re.sub(r"[^0-9]", "", review_cnt_el.text))
                except Exception:
                    review_cnt = None

            # Extract product id (if data-product-id exists)
            pid = li.get("data-product-id") or re.sub(r"\D", "", href or "") or title[:32]

            items.append(
                Product(
                    id=str(pid),
                    title=title,
                    price=price,
                    rating=rating,
                    review_cnt=review_cnt,
                    images=[],
                    url=product_url,
                    deeplink=None,
                )
            )

        return items

    def enrich_product(self, product: Product) -> Product:
        if not product.url:
            return product
        resp = get(product.url)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Try to get title, brand and images from product page
        title_el = soup.select_one("h2.prod-buy-header__title") or soup.select_one(
            "h2.prod-buy-header__title__name"
        )
        if title_el:
            product.title = title_el.get_text(strip=True)

        # Images
        imgs = []
        for img in soup.select(".prod-image__detail img, .thumbnail img"):
            src = img.get("src") or img.get("data-src")
            if src and src.startswith("http"):
                imgs.append(src)
        if imgs:
            product.images = imgs[:10]

        # Rating and reviews could be present as text
        if product.rating is None:
            rating_el = soup.select_one(".rating-star-num, .prod-buy-header__rating");
            try:
                if rating_el:
                    product.rating = float(re.search(r"[0-9]+(\.[0-9]+)?", rating_el.text).group())
            except Exception:
                pass

        if product.review_cnt is None:
            rc_el = soup.select_one(".count, .js_reviewCount")
            try:
                if rc_el:
                    product.review_cnt = int(re.sub(r"[^0-9]", "", rc_el.text))
            except Exception:
                pass

        return product
