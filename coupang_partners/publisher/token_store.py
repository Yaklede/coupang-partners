from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


BASE = Path("secrets")
BASE.mkdir(parents=True, exist_ok=True)

NAVER_APP_PATH = BASE / "naver_app.json"
NAVER_TOKEN_PATH = BASE / "naver_token.json"


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_naver_app() -> Dict[str, Any]:
    return read_json(NAVER_APP_PATH)


def save_naver_app(client_id: str, client_secret: str, redirect_uri: str) -> None:
    write_json(NAVER_APP_PATH, {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    })


def get_naver_tokens() -> Dict[str, Any]:
    return read_json(NAVER_TOKEN_PATH)


def save_naver_tokens(data: Dict[str, Any]) -> None:
    write_json(NAVER_TOKEN_PATH, data)

