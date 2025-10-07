from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db import get_session
from app.models import Metrics, Post, Budget


router = APIRouter()


@router.get("/posts")
async def metrics_posts(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(func.count(Post.id)))
    total_posts = res.scalar() or 0
    res = await session.execute(select(func.count(Post.id)).where(Post.status == "published"))
    published = res.scalar() or 0
    return {"total": total_posts, "published": published}


@router.get("/budget")
async def metrics_budget(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Budget))
    rows = [dict(date=b.date, token_used=b.token_used, usd_spent=b.usd_spent, cap=b.cap) for b in res.scalars()]
    return {"daily": rows}

