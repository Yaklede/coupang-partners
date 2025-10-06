from __future__ import annotations

import datetime as dt
from typing import List, Dict, Any, Optional

import requests

from ..publisher.token_store import get_naver_app


DL_URL = "https://openapi.naver.com/v1/datalab/search"


def datalab_search(seed_keywords: List[str], days: int = 30, time_unit: str = "date") -> Optional[Dict[str, Any]]:
    app = get_naver_app()
    cid = app.get("client_id")
    cs = app.get("client_secret")
    if not (cid and cs):
        return None

    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    payload = {
        "startDate": start.strftime("%Y-%m-%d"),
        "endDate": end.strftime("%Y-%m-%d"),
        "timeUnit": time_unit,
        "keywordGroups": [
            {"groupName": kw, "keywords": [kw]} for kw in seed_keywords if kw
        ],
        # device/ages/gender optional
    }
    headers = {
        "X-Naver-Client-Id": cid,
        "X-Naver-Client-Secret": cs,
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(DL_URL, json=payload, headers=headers, timeout=20)
        if r.status_code >= 400:
            return None
        return r.json()
    except Exception:
        return None


def trending_seeds_from_datalab(seed_categories: List[str], topk: int = 3) -> List[str]:
    data = datalab_search(seed_categories)
    if not data:
        return seed_categories[:topk]
    scored: List[tuple[str, float]] = []
    for res in data.get("results", []):
        group = res.get("title") or res.get("keyword") or res.get("keywordGroups") or ""
        series = res.get("data", [])
        if not series:
            continue
        # score: last value minus median of previous half
        vals = [float(d.get("ratio", 0.0)) for d in series]
        if not vals:
            continue
        last = vals[-1]
        prev = vals[:-1] or [0]
        prev = prev[len(prev)//2:]
        baseline = sum(prev)/len(prev)
        score = last - baseline
        name = res.get("title") or res.get("keywords", [group])[0]
        scored.append((str(name), score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored[:topk]] or seed_categories[:topk]


def datalab_trend_context(seed_keywords: List[str], days: int = 30) -> Optional[Dict[str, Any]]:
    """Return a compact trend context for LLM prompting: each keyword with last ratio and delta."""
    data = datalab_search(seed_keywords, days=days)
    if not data:
        return None
    ctx: Dict[str, Any] = {"window_days": days, "keywords": []}
    for res in data.get("results", []):
        series = res.get("data", [])
        if not series:
            continue
        vals = [float(d.get("ratio", 0.0)) for d in series]
        last = vals[-1]
        prev = vals[:-1] or [0]
        prev = prev[len(prev)//2:]
        baseline = sum(prev)/len(prev)
        delta = last - baseline
        name = res.get("title") or res.get("keywords", [""])[0]
        ctx["keywords"].append({"keyword": name, "last_ratio": last, "delta": delta})
    return ctx
