from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_session
from app.models import AffiliateMap, ProductCandidate
from app.schemas import AffiliateMapCreate
from app.utils.urls import build_coupang_search_url


router = APIRouter()


@router.post("/map")
async def map_affiliate(payload: AffiliateMapCreate, session: AsyncSession = Depends(get_session)):
    pc = await session.get(ProductCandidate, payload.product_id)
    if not pc:
        raise HTTPException(404, "product not found")
    am = AffiliateMap(product_candidate_id=pc.id, affiliate_url=payload.url, affiliate_html=payload.html)
    pc.status = "mapped"
    session.add(am)
    await session.commit()
    return {"ok": True, "id": am.id}


@router.get("/pending")
async def pending(session: AsyncSession = Depends(get_session)):
    q = select(ProductCandidate).where(ProductCandidate.status == "pending").order_by(ProductCandidate.id.desc())
    res = await session.execute(q)
    items = []
    for pc in res.scalars():
        items.append({
            "id": pc.id,
            "keyword_id": pc.keyword_id,
            "title_guess": pc.title_guess,
            "brand": pc.brand,
            "model": pc.model,
            "coupang_url": build_coupang_search_url(pc.title_guess, pc.brand, pc.model, None),
        })
    return items
