from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

BASE = Path("secrets")
PATH = BASE / "affiliate_links.json"


def _load() -> Dict[str, str]:
    if not PATH.exists():
        return {}
    try:
        return json.loads(PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: Dict[str, str]) -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_affiliate(raw_url: str) -> Optional[str]:
    data = _load()
    return data.get(raw_url)


def put_affiliate(raw_url: str, affiliate_url: str) -> None:
    data = _load()
    data[raw_url] = affiliate_url
    _save(data)


def all_affiliates() -> Dict[str, str]:
    return _load()

