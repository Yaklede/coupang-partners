from __future__ import annotations

import os
from typing import Optional

from .miner.coupang_api import CoupangApiMiner


def generate_affiliate_link(raw_url: str, method: str = "none") -> Optional[str]:
    """Return affiliate link by selected method.

    method:
      - none: return None (no affiliate)
      - partners_api: TODO integrate official Partners Open API (requires keys)
      - portal: TODO login automation (not implemented for safety/compliance)
    """
    method = (method or "none").lower()
    if not raw_url:
        return None
    if method == "none":
        return None
    if method == "partners_api":
        miner = CoupangApiMiner()
        out = miner.deeplink([raw_url])
        return out[0] if out else None
    if method == "portal":
        # Placeholder: not implemented due to login/2FA/compliance concerns.
        return None
    return None
