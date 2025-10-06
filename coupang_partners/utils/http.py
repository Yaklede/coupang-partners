from __future__ import annotations

import random
import time
from typing import Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
try:
    from fake_useragent import UserAgent
except Exception:
    UserAgent = None


def default_headers(mobile: bool = False) -> Dict[str, str]:
    ua = UserAgent() if UserAgent else None
    desktop = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    return {
        "User-Agent": (ua.random if ua else (mobile_ua if mobile else desktop)),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
    }


def _session_with_retries(total: int = 2, backoff: float = 0.5) -> requests.Session:
    sess = requests.Session()
    retry = Retry(
        total=total,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    sess.mount("http://", adapter)
    sess.mount("https://", adapter)
    return sess


def get(url: str, headers: Optional[Dict[str, str]] = None, delay_range=(0.5, 1.5), timeout: tuple = (10, 15)) -> requests.Response:
    time.sleep(random.uniform(*delay_range))
    sess = _session_with_retries()
    hdrs = default_headers()
    if headers:
        hdrs.update(headers)
    resp = sess.get(url, headers=hdrs, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()
    return resp
