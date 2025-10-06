from __future__ import annotations

import random
import time
from typing import Dict, Optional

import requests
try:
    from fake_useragent import UserAgent
except Exception:
    UserAgent = None


def default_headers() -> Dict[str, str]:
    ua = UserAgent() if UserAgent else None
    return {
        "User-Agent": (ua.random if ua else "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
    }


def get(url: str, headers: Optional[Dict[str, str]] = None, delay_range=(0.5, 1.5)) -> requests.Response:
    time.sleep(random.uniform(*delay_range))
    sess = requests.Session()
    hdrs = default_headers()
    if headers:
        hdrs.update(headers)
    resp = sess.get(url, headers=hdrs, timeout=20)
    resp.raise_for_status()
    return resp
