from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.db import get_session
from app.models import Post, ProductCandidate, AffiliateMap, Keyword
from app.schemas import PostDraftCreate, PostPublish, PostOut, PostDraftCompare
from app.services.post_writer import generate_post_markdown
from app.services.publisher import schedule_post, publish_now
from app.utils.errors import AIError
from app.services.specs import fetch_coupang_product_specs, build_spec_table
from app.services.analyzer import analyze_alignment


router = APIRouter()


@router.post("/draft")
async def create_draft(payload: PostDraftCreate, session: AsyncSession = Depends(get_session)):
    pc = await session.get(ProductCandidate, payload.product_id)
    if not pc:
        raise HTTPException(404, "product not found")
    # check affiliate
    amap = await session.execute(select(AffiliateMap).where(AffiliateMap.product_candidate_id == pc.id))
    amap = amap.scalars().first()
    if not amap:
        raise HTTPException(400, "affiliate mapping required")
    kw = await session.get(Keyword, pc.keyword_id)
    # enrich single-product with basic spec table if available
    spec_table_md = None
    sources = []
    if amap and amap.affiliate_url and 'coupang.com' in amap.affiliate_url:
        try:
            spec = await fetch_coupang_product_specs(amap.affiliate_url)
            if spec and spec.get('specs'):
                spec_table_md = build_spec_table([{ 'name': pc.title_guess or '', 'specs': spec.get('specs', {}), 'feature': (pc.why or '') }])
                if spec.get('source_url'):
                    sources.append(spec.get('source_url'))
        except Exception:
            pass
    # analyze alignment based on mapped info
    alignment = await analyze_alignment(
        brand=pc.brand, model=pc.model, title_guess=pc.title_guess,
        affiliate_url=amap.affiliate_url, affiliate_html=amap.affiliate_html,
        keyword=(kw.text if kw else ""),
    )
    try:
        md, title, tags, images, template_id = await generate_post_markdown(
            keyword=kw.text if kw else "",
            candidate=pc,
            affiliate_url=amap.affiliate_url,
            affiliate_html=amap.affiliate_html,
            template_type=payload.template_type or "A",
            template_input={**alignment, **(payload.template_input or {}), **({"spec_table_md": spec_table_md, "sources": sources} if spec_table_md else {})},
        )
    except AIError as e:
        status = 400 if e.code == 'config_error' else 502
        raise HTTPException(status_code=status, detail=e.to_dict())
    import json
    post = Post(keyword_id=pc.keyword_id, product_candidate_id=pc.id, title=title, body_md=md, tags=",".join(tags), images=",".join(images), status="draft", template_id=template_id, meta_json=json.dumps({"alignment": alignment}, ensure_ascii=False))
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return {"id": post.id, "title": post.title}


@router.post("/publish")
async def publish(payload: PostPublish, session: AsyncSession = Depends(get_session)):
    post = await session.get(Post, payload.post_id)
    if not post:
        raise HTTPException(404, "post not found")
    if payload.schedule:
        when = datetime.fromisoformat(payload.schedule)
        await schedule_post(post.id, when, session)
    else:
        await publish_now(post.id, session)
    return {"ok": True}


@router.get("", response_model=list[PostOut])
async def list_posts(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Post).order_by(Post.id.desc()).limit(200))
    return list(res.scalars())


@router.post("/draft/compare")
async def create_compare_draft(payload: PostDraftCompare, session: AsyncSession = Depends(get_session)):
    if not payload.product_ids or len(payload.product_ids) < 2:
        raise HTTPException(400, "at least 2 product_ids required")
    # gather candidates (first 4)
    pcs: list[ProductCandidate] = []
    for pid in payload.product_ids[:4]:
        pc = await session.get(ProductCandidate, pid)
        if pc:
            pcs.append(pc)
    if len(pcs) < 2:
        raise HTTPException(400, "not enough valid products")
    # build spec table
    rows = []
    sources = []
    for pc in pcs:
        amap = await session.execute(select(AffiliateMap).where(AffiliateMap.product_candidate_id == pc.id))
        amap = amap.scalars().first()
        spec = {}
        if amap and amap.affiliate_url and 'coupang.com' in amap.affiliate_url:
            try:
                data = await fetch_coupang_product_specs(amap.affiliate_url)
                spec = data.get('specs', {})
                if data.get('source_url'):
                    sources.append(data.get('source_url'))
            except Exception:
                pass
        rows.append({ 'name': pc.title_guess or f"{pc.brand or ''} {pc.model or ''}", 'specs': spec, 'feature': pc.why or '' })
    spec_table_md = build_spec_table(rows)
    # pick keyword from first candidate
    kw = await session.get(Keyword, pcs[0].keyword_id)
    first_map = await session.execute(select(AffiliateMap).where(AffiliateMap.product_candidate_id == pcs[0].id))
    first_map = first_map.scalars().first()
    try:
        md, title, tags, images, template_id = await generate_post_markdown(
            keyword=kw.text if kw else "",
            candidate=pcs[0],
            affiliate_url=(first_map.affiliate_url if first_map else ""),
            affiliate_html=(first_map.affiliate_html if first_map else None),
            template_type="B",
            template_input={**(payload.template_input or {}), "items": [r['name'] for r in rows], "spec_table_md": spec_table_md, "sources": list(dict.fromkeys(sources))[:4]},
        )
    except AIError as e:
        status = 400 if e.code == 'config_error' else 502
        raise HTTPException(status_code=status, detail=e.to_dict())
    post = Post(keyword_id=pcs[0].keyword_id, product_candidate_id=pcs[0].id, title=title, body_md=md, tags=",".join(tags), images=",".join(images), status="draft", template_id=template_id)
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return {"id": post.id, "title": post.title}
