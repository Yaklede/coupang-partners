from __future__ import annotations

import os
from typing import Literal

from .base import ProductMiner
from .coupang_api import CoupangApiMiner
from .coupang_crawler import CoupangCrawlerMiner


def select_coupang_miner(mode: Literal["crawler", "api", "auto"] = "auto") -> ProductMiner:
    mode = (mode or "auto").lower()
    if mode == "crawler":
        return CoupangCrawlerMiner()
    if mode == "api":
        return CoupangApiMiner()
    # auto: choose api if keys present else crawler
    has_keys = bool(os.getenv("COUPANG_OPENAPI_ACCESS_KEY") and os.getenv("COUPANG_OPENAPI_SECRET_KEY"))
    return CoupangApiMiner() if has_keys else CoupangCrawlerMiner()

