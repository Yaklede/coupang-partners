import os
import time
import json
import datetime as dt
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.settings import settings
from app.db import AsyncSessionLocal
from app.models import NaverToken


AUTH_BASE = "https://nid.naver.com/oauth2.0"
API_BASE = "https://openapi.naver.com/v1"


def naver_login_url() -> str:
    client_id = settings.NAVER_CLIENT_ID or ""
    redirect_uri = settings.NAVER_REDIRECT_URI or ""
    state = "naver-state"
    return (
        f"{AUTH_BASE}/authorize?response_type=code&client_id={client_id}"
        f"&redirect_uri={redirect_uri}&state={state}"
    )


async def handle_callback(code: str | None, state: str | None) -> bool:
    if not code:
        return False
    async with httpx.AsyncClient(timeout=20) as client:
        res = await client.get(
            f"{AUTH_BASE}/token",
            params={
                "grant_type": "authorization_code",
                "client_id": settings.NAVER_CLIENT_ID,
                "client_secret": settings.NAVER_CLIENT_SECRET,
                "code": code,
                "state": state or "",
            },
        )
    if res.status_code != 200:
        return False
    data = res.json()
    expires_at = dt.datetime.utcnow() + dt.timedelta(seconds=int(data.get("expires_in", 0)))
    async with AsyncSessionLocal() as session:
        tok = NaverToken(access_token=data.get("access_token"), refresh_token=data.get("refresh_token"), token_type=data.get("token_type"), expires_at=expires_at)
        session.add(tok)
        await session.commit()
    return True


async def token_status():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(NaverToken).order_by(NaverToken.id.desc()))
        tok = res.scalars().first()
        if not tok:
            return {"connected": False}
        return {
            "connected": True,
            "expires_at": tok.expires_at.isoformat() if tok.expires_at else None,
        }


async def publish_blog_post(title: str, content: str) -> str | None:
    # Requires a valid access token in DB
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(NaverToken).order_by(NaverToken.id.desc()))
        tok = res.scalars().first()
    if not tok or not tok.access_token:
        return None
    headers = {"Authorization": f"Bearer {tok.access_token}"}
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(
            f"{API_BASE}/blog/writePost.json",
            headers=headers,
            data={
                "title": title,
                "contents": content,
                "blogId": settings.NAVER_BLOG_ID or "",
            },
        )
    if res.status_code != 200:
        return None
    data = res.json()
    return str(data.get("postId") or data.get("result", {}).get("postId"))

