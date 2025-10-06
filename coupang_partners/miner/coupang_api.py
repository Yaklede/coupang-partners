from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import os
import urllib.parse
from typing import List, Optional

import requests

from ..models import Product


class CoupangApiMiner:
    """
    Minimal Coupang Partners Open API client for product search and deeplink.

    Note: This implementation expects the following env vars:
      - COUPANG_OPENAPI_ACCESS_KEY
      - COUPANG_OPENAPI_SECRET_KEY
      - COUPANG_PARTNER_ID (for deeplink suffix)

    The actual Open API endpoints and authentication are subject to Coupang docs.
    We implement a generic HMAC auth header creator; you should verify endpoints
    and adjust the path patterns according to your account region.
    """

    HOST = "https://api-gateway.coupang.com"

    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None, partner_id: Optional[str] = None):
        self.access_key = access_key or os.getenv("COUPANG_OPENAPI_ACCESS_KEY")
        self.secret_key = secret_key or os.getenv("COUPANG_OPENAPI_SECRET_KEY")
        self.partner_id = partner_id or os.getenv("COUPANG_PARTNER_ID")

    def _has_keys(self) -> bool:
        return bool(self.access_key and self.secret_key)

    def _authorization(self, method: str, path: str, query: str = "") -> str:
        # Generic HMAC SHA256 signature builder.
        datetime_gmt = dt.datetime.utcnow().strftime("%y%m%dT%H%M%SZ")
        message = datetime_gmt + method + path + query
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        signature_b64 = base64.b64encode(signature).decode("utf-8")
        return f"CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={datetime_gmt}, signature={signature_b64}"

    def _get(self, path: str, params: dict) -> requests.Response:
        query = "?" + urllib.parse.urlencode(params) if params else ""
        headers = {"Authorization": self._authorization("GET", path, query)}
        url = f"{self.HOST}{path}{query}"
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        return resp

    def search_products(self, keyword: str, limit: int = 10) -> List[Product]:
        if not self._has_keys():
            return []

        # Placeholder endpoint path. Adjust per Coupang Open API documentation.
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": limit}
        try:
            resp = self._get(path, params)
            data = resp.json()
        except Exception:
            return []

        items: List[Product] = []
        for it in (data.get("products") or [])[:limit]:
            pid = str(it.get("productId")) if it.get("productId") else it.get("id")
            url = it.get("productUrl") or it.get("url")
            deeplink = url
            if self.partner_id and url:
                sep = "&" if ("?" in url) else "?"
                deeplink = f"{url}{sep}src=blog&partner={self.partner_id}&keyword={urllib.parse.quote(keyword)}"

            items.append(
                Product(
                    id=str(pid or ""),
                    title=str(it.get("productName") or it.get("title") or ""),
                    brand=it.get("brand"),
                    category=[c for c in it.get("category") or [] if c],
                    price=float(it.get("price")) if it.get("price") else None,
                    rating=float(it.get("rating")) if it.get("rating") else None,
                    review_cnt=int(it.get("reviewCount")) if it.get("reviewCount") else None,
                    images=[img for img in it.get("images") or [] if img],
                    deeplink=deeplink,
                    url=url,
                )
            )

        return items

    def enrich_product(self, product: Product) -> Product:
        # For API, assume search already returns most fields. No-op for now.
        return product

