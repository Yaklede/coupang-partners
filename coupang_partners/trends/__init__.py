from __future__ import annotations

from typing import List

from ..config import Settings
from .naver_datalab import trending_seeds_from_datalab
from ..keywords import generate_keywords


def generate_trending_keywords(settings: Settings, count: int = 10) -> List[str]:
    seeds = settings.keywords.seed_categories or ["가전", "주방", "리빙", "디지털"]
    try:
        hot = trending_seeds_from_datalab(seeds, topk=min(3, len(seeds)))
        # Use trending seeds to bias keyword generation
        original = settings.keywords.seed_categories
        settings.keywords.seed_categories = hot
        kws = generate_keywords(settings)
        # restore
        settings.keywords.seed_categories = original
        if kws:
            return kws[:count]
    except Exception:
        pass
    # fallback to base generator
    return generate_keywords(settings)[:count]

