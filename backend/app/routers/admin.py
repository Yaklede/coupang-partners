from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db import get_session, engine, Base
from app.services.config import get_ai_config_dict, set_ai_config_dict


router = APIRouter()


@router.post("/reset-db")
async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"ok": True, "message": "database dropped and recreated"}


@router.delete("/keywords")
async def delete_keywords(date: str | None = Query(None, description="YYYY-MM-DD; if omitted, delete all"), session: AsyncSession = Depends(get_session)):
    if date:
        # Manual cascade deletes for SQLite safety
        await session.execute(text(
            "DELETE FROM affiliate_map WHERE product_candidate_id IN ("
            "  SELECT pc.id FROM product_candidate pc JOIN keyword k ON pc.keyword_id = k.id WHERE k.date_range = :d)"
        ), {"d": date})
        await session.execute(text(
            "DELETE FROM post WHERE keyword_id IN (SELECT id FROM keyword WHERE date_range = :d)"
        ), {"d": date})
        await session.execute(text(
            "DELETE FROM product_candidate WHERE keyword_id IN (SELECT id FROM keyword WHERE date_range = :d)"
        ), {"d": date})
        res = await session.execute(text("DELETE FROM keyword WHERE date_range = :d"), {"d": date})
        await session.commit()
        return {"ok": True, "deleted_date": date}
    else:
        # Full wipe of keyword-related tables
        await session.execute(text("DELETE FROM affiliate_map"))
        await session.execute(text("DELETE FROM post"))
        await session.execute(text("DELETE FROM product_candidate"))
        await session.execute(text("DELETE FROM keyword"))
        await session.commit()
        return {"ok": True, "deleted": "all keywords & related"}


@router.post("/dedup-keywords")
async def dedup_keywords(date: str = Query(..., description="YYYY-MM-DD"), session: AsyncSession = Depends(get_session)):
    # Keep the latest row per text for the date, delete others
    # SQLite-compatible multi-step approach.
    await session.execute(text(
        "DELETE FROM keyword WHERE date_range = :d AND id NOT IN ("
        "  SELECT MAX(id) FROM keyword WHERE date_range = :d GROUP BY text"
        ")"
    ), {"d": date})
    await session.commit()
    return {"ok": True, "deduped_date": date}


@router.get("/ai-config")
async def ai_config_get():
    return await get_ai_config_dict()


@router.post("/ai-config")
async def ai_config_set(payload: dict):
    await set_ai_config_dict(payload or {})
    return await get_ai_config_dict()
