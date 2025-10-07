from fastapi import APIRouter, Depends
from app.services.naver import naver_login_url, handle_callback, token_status


router = APIRouter()


@router.get("/naver/login")
async def naver_login():
    return {"login_url": naver_login_url()}


@router.get("/naver/callback")
async def naver_callback(code: str | None = None, state: str | None = None):
    ok = await handle_callback(code, state)
    return {"ok": ok}


@router.get("/naver/status")
async def naver_status():
    return await token_status()

