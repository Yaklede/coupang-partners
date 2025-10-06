from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv


@dataclass
class AppConfig:
    target_posts_per_day: int = 3
    burst_window_minutes: int = 90
    random_delay_sec: tuple[int, int] = (15, 120)
    locale: str = "ko_KR"
    timezone: str = "Asia/Seoul"


@dataclass
class CostConfig:
    monthly_cap_usd: float = 20.0
    daily_cap_usd: float = 0.67


@dataclass
class PostingConfig:
    mode: str = "draft"  # draft | public
    default_category_no: int = 0
    hashtags: list[str] | None = None
    roundup_list_post_items_min: int = 3
    roundup_list_post_items_max: int = 7


@dataclass
class StorageConfig:
    url: str = "sqlite:///app.db"
    echo: bool = False


@dataclass
class ProvidersConfig:
    openai_model: str = "gpt-4o-mini"


@dataclass
class CoupangSourceConfig:
    # mode: crawler | api | auto
    mode: str = "crawler"


@dataclass
class KeywordsConfig:
    daily_count: int = 3
    seed_categories: List[str] | None = None
    fallback_list: List[str] | None = None

@dataclass
class AffiliateConfig:
    generation: str = "none"  # none | partners_api | portal
    require_for_publish: bool = True


@dataclass
class Settings:
    app: AppConfig
    cost: CostConfig
    posting: PostingConfig
    storage: StorageConfig
    providers: ProvidersConfig
    coupang_source: CoupangSourceConfig
    keywords: KeywordsConfig
    affiliate: AffiliateConfig


def _dict_get(d: Dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = d
    for key in path.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def load_settings(path: str | None = None) -> Settings:
    load_dotenv(override=False)

    cfg: Dict[str, Any] = {}
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    elif os.path.exists("config.yaml"):
        with open("config.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

    app = AppConfig(
        target_posts_per_day=int(_dict_get(cfg, "app.target_posts_per_day", 3)),
        burst_window_minutes=int(_dict_get(cfg, "app.burst_window_minutes", 90)),
        random_delay_sec=tuple(_dict_get(cfg, "app.random_delay_sec", [15, 120])),
        locale=_dict_get(cfg, "app.locale", "ko_KR"),
        timezone=_dict_get(cfg, "app.timezone", "Asia/Seoul"),
    )

    cost = CostConfig(
        monthly_cap_usd=float(_dict_get(cfg, "cost.monthly_cap_usd", 20.0)),
        daily_cap_usd=float(_dict_get(cfg, "cost.daily_cap_usd", 0.67)),
    )

    posting = PostingConfig(
        mode=_dict_get(cfg, "posting.mode", "draft"),
        default_category_no=int(_dict_get(cfg, "posting.default_category_no", 0)),
        hashtags=list(_dict_get(cfg, "posting.hashtags", ["리뷰", "쇼핑", "추천"])),
        roundup_list_post_items_min=int(
            _dict_get(cfg, "posting.roundup.list_post_items_min", 3)
        ),
        roundup_list_post_items_max=int(
            _dict_get(cfg, "posting.roundup.list_post_items_max", 7)
        ),
    )

    storage = StorageConfig(
        url=_dict_get(cfg, "storage.url", "sqlite:///app.db"),
        echo=bool(_dict_get(cfg, "storage.echo", False)),
    )

    providers = ProvidersConfig(
        openai_model=_dict_get(cfg, "providers.openai.model", "gpt-4o-mini")
    )

    coupang_source = CoupangSourceConfig(
        mode=_dict_get(cfg, "coupang_source.mode", "crawler")
    )

    keywords = KeywordsConfig(
        daily_count=int(_dict_get(cfg, "keywords.daily_count", 3)),
        seed_categories=list(_dict_get(cfg, "keywords.seed_categories", ["가전", "주방", "리빙", "디지털"])),
        fallback_list=list(_dict_get(cfg, "keywords.fallback_list", ["가습기", "제습기", "무선 청소기", "에어프라이어", "전기포트"])),
    )

    affiliate = AffiliateConfig(
        generation=_dict_get(cfg, "affiliate.generation", "none"),
        require_for_publish=bool(_dict_get(cfg, "affiliate.require_for_publish", True)),
    )

    return Settings(
        app=app,
        cost=cost,
        posting=posting,
        storage=storage,
        providers=providers,
        coupang_source=coupang_source,
        keywords=keywords,
        affiliate=affiliate,
    )
