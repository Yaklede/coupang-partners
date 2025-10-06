from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set


BASE = Path("secrets")
POSTED = BASE / "posted.json"


def _load_posted() -> Dict[str, bool]:
    if not POSTED.exists():
        return {}
    try:
        return json.loads(POSTED.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_posted(d: Dict[str, bool]) -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    POSTED.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def mark_posted(urls: List[str]) -> None:
    d = _load_posted()
    for u in urls:
        d[u] = True
    _save_posted(d)


def posted_set() -> Set[str]:
    return set([k for k, v in _load_posted().items() if v])

