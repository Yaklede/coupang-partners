from __future__ import annotations

import json
from typing import Optional

import typer

from .config import load_settings
from .miner import select_coupang_miner
from .models import ProductSearchResult
from .orchestrator import run_once


app = typer.Typer(help="Coupang Partners automation CLI (miner focus)")


@app.command()
def search(
    keyword: str = typer.Argument(..., help="검색 키워드"),
    limit: int = typer.Option(5, help="검색 결과 최대 개수"),
    mode: Optional[str] = typer.Option(
        None, help="coupang source: crawler | api | auto (default from config)"
    ),
    config: Optional[str] = typer.Option(None, help="경로: config.yaml"),
):
    """쿠팡 상품 검색(JSON 출력)."""
    settings = load_settings(config)
    source_mode = mode or settings.coupang_source.mode or "crawler"
    miner = select_coupang_miner(source_mode)
    items = miner.search_products(keyword, limit=limit)
    result = ProductSearchResult(keyword=keyword, items=items)
    typer.echo(result.to_json(ensure_ascii=False))


@app.command()
def enrich(
    product_json: str = typer.Argument(..., help="Product JSON (단일)"),
    mode: Optional[str] = typer.Option(None, help="crawler | api | auto"),
    config: Optional[str] = typer.Option(None, help="경로: config.yaml"),
):
    """상품 상세 정보 보강(JSON 입력→JSON 출력)."""
    from .models import Product

    settings = load_settings(config)
    source_mode = mode or settings.coupang_source.mode or "crawler"
    miner = select_coupang_miner(source_mode)

    p = Product.from_json(product_json)
    p2 = miner.enrich_product(p)
    typer.echo(p2.to_json(ensure_ascii=False))


@app.command()
def run(
    count: int = typer.Option(None, help="생성/게시할 포스트 수(기본: config.app.target_posts_per_day)"),
    mode: Optional[str] = typer.Option(None, help="coupang source: crawler | api | auto"),
    config: Optional[str] = typer.Option(None, help="경로: config.yaml"),
    output: Optional[str] = typer.Option(None, help="결과 JSON 저장 경로"),
    dry_run: bool = typer.Option(False, help="게시 건너뛰고 생성만 수행"),
):
    """키워드→쿠팡→작성→리파인→SEO→네이버 게시 전체 파이프라인 1회 실행."""
    import json as _json

    res = run_once(config_path=config, count=count, mode=mode, dry_run=dry_run)
    out = _json.dumps(res, ensure_ascii=False, indent=2)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(out)
    typer.echo(out)


def main():
    app()


if __name__ == "__main__":
    main()
