from __future__ import annotations

import os
from typing import Optional, Dict, Any

import requests


from .token_store import get_naver_tokens


class NaverPublisher:
    """Minimal Naver Blog post publisher.

    Requires `NAVER_ACCESS_TOKEN` (OAuth2 user token).
    Optional: `NAVER_CLIENT_ID` and `NAVER_CLIENT_SECRET` if you handle refresh externally.

    Endpoint (subject to Naver Developers docs):
      POST https://openapi.naver.com/blog/writePost.json
      Headers: Authorization: Bearer {token}
      Form: title, contents, categoryNo (optional), tags (comma-separated)
    """

    ENDPOINT = "https://openapi.naver.com/blog/writePost.json"

    def __init__(self, access_token: Optional[str] = None):
        token = access_token or os.getenv("NAVER_ACCESS_TOKEN")
        if not token:
            t = get_naver_tokens()
            token = t.get("access_token")
        self.token = token

    def available(self) -> bool:
        return bool(self.token)

    def publish(self, title: str, html: str, category_no: Optional[int] = None, tags: Optional[list[str]] = None) -> Dict[str, Any]:
        if not self.available():
            return {"status": "skipped", "reason": "NAVER_ACCESS_TOKEN missing", "title": title}

        headers = {"Authorization": f"Bearer {self.token}"}
        data = {"title": title, "contents": html}
        if category_no is not None:
            data["categoryNo"] = str(category_no)
        if tags:
            data["tags"] = ",".join(tags)

        try:
            resp = requests.post(self.ENDPOINT, headers=headers, data=data, timeout=30)
            if resp.status_code >= 400:
                return {"status": "error", "code": resp.status_code, "body": resp.text}
            return {"status": "ok", "code": resp.status_code, "data": resp.json()}
        except Exception as e:
            return {"status": "error", "error": str(e)}
