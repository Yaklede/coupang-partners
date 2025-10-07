from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import Keyword
from app.schemas import KeywordCreate, KeywordOut
from app.services.datalab import fetch_trending_keywords


router = APIRouter()


@router.post("/fetch", response_model=list[KeywordOut])
async def fetch_keywords(session: AsyncSession = Depends(get_session)):
    items = await fetch_trending_keywords()
    if not items:
        return []
    day = items[0].get("date_range")

    # Load existing keywords for this day to deduplicate
    existing_res = await session.execute(
        select(Keyword).where(Keyword.date_range == day)
    )
    existing = {k.text: k for k in existing_res.scalars()}

    for i in items:
        text = i["text"]
        if text in existing:
            # Optional: refresh score/category/status idempotently
            k = existing[text]
            k.score = i.get("score", k.score)
            k.category = i.get("category", k.category)
            k.status = k.status or "collected"
        else:
            kw = Keyword(
                text=text,
                date_range=day,
                score=i.get("score"),
                category=i.get("category"),
                status="collected",
            )
            session.add(kw)
            existing[text] = kw

    await session.commit()

    # Return the deduped list for the day (stable across repeated calls)
    res = await session.execute(
        select(Keyword).where(Keyword.date_range == day).order_by(Keyword.id.desc())
    )
    return list(res.scalars())


@router.get("", response_model=list[KeywordOut])
async def list_keywords(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Keyword).order_by(Keyword.id.desc()).limit(200))
    return list(res.scalars())
