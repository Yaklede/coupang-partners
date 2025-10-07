from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import ProductCandidate, Keyword
from app.schemas import ProductCandidateOut
from app.services.product_scout import recommend_products
from app.utils.errors import AIError
from app.utils.urls import build_coupang_search_url


router = APIRouter()


@router.post("/recommend/{keyword_id}", response_model=list[ProductCandidateOut])
async def recommend(keyword_id: int, session: AsyncSession = Depends(get_session)):
    kw = await session.get(Keyword, keyword_id)
    if not kw:
        raise HTTPException(404, "keyword not found")
    # collect existing dedupe_keys for this keyword to reduce duplicates
    res = await session.execute(select(ProductCandidate.dedupe_key).where(ProductCandidate.keyword_id == kw.id, ProductCandidate.dedupe_key.is_not(None)))
    dedup_keys = [r for (r,) in res.all() if r]
    try:
        data = await recommend_products(kw.text, dedup_keys)
    except AIError as e:
        status = 400 if e.code == 'config_error' else 502
        raise HTTPException(status_code=status, detail=e.to_dict())
    created = []
    for d in data:
        pc = ProductCandidate(
            keyword_id=kw.id,
            title_guess=d.get("title_guess") or d.get("title"),
            brand=d.get("brand"),
            model=d.get("model"),
            price_band=d.get("price_band"),
            why=d.get("why"),
            image_hint=d.get("image_hint"),
            dedupe_key=d.get("dedupe_key"),
        )
        session.add(pc)
        # attach non-persisted field 'coupang_url' for response convenience
        pc.coupang_url = d.get("coupang_url") or build_coupang_search_url(pc.title_guess, pc.brand, pc.model, kw.text)
        created.append(pc)
    await session.commit()
    for pc in created:
        await session.refresh(pc)
    return created


@router.get("", response_model=list[ProductCandidateOut])
async def list_candidates(status: str | None = None, session: AsyncSession = Depends(get_session)):
    q = select(ProductCandidate)
    if status:
        q = q.where(ProductCandidate.status == status)
    q = q.order_by(ProductCandidate.id.desc()).limit(200)
    res = await session.execute(q)
    items = list(res.scalars())
    # attach computed coupang_url
    for it in items:
        it.coupang_url = build_coupang_search_url(it.title_guess, it.brand, it.model, None)
    return items
