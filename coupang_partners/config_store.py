from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def read_config(path: str | None = None) -> Dict[str, Any]:
    p = Path(path or "config.yaml")
    if not p.exists():
        # try example as a starting point
        ex = Path("config.example.yaml")
        return yaml.safe_load(ex.read_text(encoding="utf-8")) if ex.exists() else {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def write_config(cfg: Dict[str, Any], path: str | None = None) -> None:
    p = Path(path or "config.yaml")
    p.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")

