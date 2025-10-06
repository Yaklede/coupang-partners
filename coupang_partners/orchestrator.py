from __future__ import annotations

from dataclasses import asdict
from typing import List

from .config import load_settings
from .keywords import generate_keywords
from .miner import select_coupang_miner
from .models import Product
from .writer import build_rag, write_post, refine_post, seo_optimize, inject_disclosure, ensure_cta, render_minimal_html
from .links import generate_affiliate_link
from .publisher.naver import NaverPublisher


def run_once(config_path: str | None = None, count: int | None = None, mode: str | None = None, dry_run: bool = False) -> List[dict]:
    settings = load_settings(config_path)
    num_posts = count or settings.app.target_posts_per_day or 1
    miner_mode = mode or settings.coupang_source.mode or "crawler"

    # 1) Keywords via OpenAI (with fallback)
    keywords = generate_keywords(settings)
    keywords = keywords[:num_posts]

    miner = select_coupang_miner(miner_mode)
    results: List[dict] = []

    publisher = NaverPublisher()

    for kw in keywords:
        # 2) Search product(s)
        items = miner.search_products(kw, limit=5)
        if not items:
            results.append({"keyword": kw, "status": "no_products"})
            continue
        # choose top candidate
        product = items[0]
        product = miner.enrich_product(product)
        # Try to ensure affiliate deeplink according to config
        aff = generate_affiliate_link(product.url or "", method=settings.affiliate.generation)
        if aff:
            product.deeplink = aff

        # 3) RAG build
        rag = build_rag(asdict(product))

        # 4~6) Writer/Refiner/SEO with graceful fallback
        try:
            html = write_post(settings.providers.openai_model, rag)
            html = refine_post(settings.providers.openai_model, html)
            seo = seo_optimize(settings.providers.openai_model, html, [kw])
            title = seo.get("title") or product.title or kw
            improved_html = seo.get("html", html)
            hashtags = seo.get("hashtags", [])
        except Exception:
            # Fallback minimal HTML without LLM
            html = render_minimal_html(rag["product"])  # type: ignore[index]
            title = product.title or kw
            improved_html = html
            hashtags = [kw]

        improved_html = ensure_cta(improved_html, product.deeplink or product.url or "")
        final_html = inject_disclosure(improved_html)

        # 7) Publisher
        if settings.affiliate.require_for_publish and not (product.deeplink):
            pub = {"status": "skipped", "reason": "no_affiliate_link"}
        elif dry_run:
            pub = {"status": "skipped", "reason": "dry_run"}
        else:
            pub = publisher.publish(title=title, html=final_html, category_no=settings.posting.default_category_no, tags=hashtags)

        results.append({
            "keyword": kw,
            "product": asdict(product),
            "title": title,
            "hashtags": hashtags,
            "publish": pub,
        })

    return results
