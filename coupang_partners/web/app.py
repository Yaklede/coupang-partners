from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import os
import secrets
import urllib.parse
import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from ..config import load_settings
from ..config_store import read_config, write_config
from ..publisher.token_store import (
    get_naver_app,
    save_naver_app,
    get_naver_tokens,
    save_naver_tokens,
)
from ..orchestrator import run_once


app = FastAPI(title="Coupang Partners GUI")


def _load_config_path() -> Optional[str]:
    return "config.yaml" if Path("config.yaml").exists() else "config.example.yaml"


@app.get("/", response_class=HTMLResponse)
def index():
    s = load_settings(_load_config_path())
    mode = s.coupang_source.mode
    model = s.providers.openai_model
    kw_count = s.keywords.daily_count
    posting_mode = s.posting.mode
    html = f"""
    <!doctype html>
    <html lang='ko'>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width, initial-scale=1'>
      <title>Coupang Partners GUI</title>
      <style>
        body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; max-width: 880px; margin: 2rem auto; padding: 0 1rem; }}
        header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; }}
        form, .card {{ border:1px solid #ddd; padding:1rem; border-radius:8px; margin-bottom:1rem; }}
        label {{ display:block; margin:.5rem 0 .25rem; }}
        input, select {{ width:100%; padding:.5rem; }}
        button {{ padding:.5rem 1rem; border:0; background:#222; color:#fff; border-radius:6px; cursor:pointer; }}
        pre {{ white-space: pre-wrap; background:#f6f6f6; padding:1rem; border-radius:8px; }}
      </style>
    </head>
    <body>
      <header>
        <h2>쿠팡 파트너스 — 자동 발행 GUI</h2>
      </header>

      <div class='card'>
        <h3>빠른 실행</h3>
        <form onsubmit="runPipeline(event)">
          <label>생성/게시 개수</label>
          <input type='number' name='count' value='{kw_count}' min='1' max='20' />

          <label>쿠팡 소스 모드</label>
          <select name='mode'>
            <option value='crawler' {'selected' if mode=='crawler' else ''}>crawler</option>
            <option value='api' {'selected' if mode=='api' else ''}>api</option>
            <option value='auto' {'selected' if mode=='auto' else ''}>auto</option>
          </select>

          <label>게시 모드</label>
          <select name='posting_mode'>
            <option value='draft' {'selected' if posting_mode=='draft' else ''}>draft</option>
            <option value='public' {'selected' if posting_mode=='public' else ''}>public</option>
          </select>

          <label>OpenAI 모델</label>
          <input name='model' value='{model}' />

          <label><input type='checkbox' name='dry_run' /> 게시 건너뛰기(dry-run)</label>

          <div style='margin-top:1rem'>
            <button type='submit'>실행</button>
          </div>
        </form>
      </div>

      <div class='card'>
        <h3>기본 설정 저장(config.yaml)</h3>
        <form onsubmit="saveConfig(event)">
          <label>OpenAI 모델</label>
          <input name='providers.openai.model' value='{model}' />

          <label>키워드 일일 개수</label>
          <input type='number' name='keywords.daily_count' value='{kw_count}' min='1' max='20' />

          <label>쿠팡 소스 모드</label>
          <select name='coupang_source.mode'>
            <option value='crawler' {'selected' if mode=='crawler' else ''}>crawler</option>
            <option value='api' {'selected' if mode=='api' else ''}>api</option>
            <option value='auto' {'selected' if mode=='auto' else ''}>auto</option>
          </select>

          <label>게시 모드</label>
          <select name='posting.mode'>
            <option value='draft' {'selected' if posting_mode=='draft' else ''}>draft</option>
            <option value='public' {'selected' if posting_mode=='public' else ''}>public</option>
          </select>

          <div style='margin-top:1rem'>
            <button type='submit'>설정 저장</button>
          </div>
        </form>
        <small>민감한 비밀키(.env)는 여기서 다루지 않습니다.</small>
      </div>

      <div class='card'>
        <h3>네이버 연결(OAuth)</h3>
        <form onsubmit="saveNaverApp(event)">
          <label>Client ID</label>
          <input name='client_id' id='naver_client_id' />
          <label>Client Secret</label>
          <input name='client_secret' id='naver_client_secret' />
          <label>Redirect URI (개발자센터에 등록)</label>
          <input name='redirect_uri' id='naver_redirect_uri' value='http://localhost:8000/oauth/naver/callback' />
          <div style='margin-top:1rem'>
            <button type='submit'>자격증명 저장</button>
            <a id='naver_connect' href='/oauth/naver/start' style='margin-left:8px'>네이버 연결</a>
          </div>
          <small>액세스 토큰은 로컬 secrets/naver_token.json에 저장됩니다.</small>
        </form>
        <pre id='naver_status'>상태 확인 중…</pre>
      </div>

      <div class='card'>
        <h3>결과</h3>
        <pre id='out'>아직 실행하지 않았습니다.</pre>
      </div>

      <script>
        async function runPipeline(e) {{
          e.preventDefault();
          const fd = new FormData(e.target);
          const payload = Object.fromEntries(fd.entries());
          payload.dry_run = fd.get('dry_run') === 'on';
          const res = await fetch('/api/run', {{ method: 'POST', headers: {{'Content-Type':'application/json'}}, body: JSON.stringify(payload) }});
          const data = await res.json();
          document.getElementById('out').textContent = JSON.stringify(data, null, 2);
        }}

        async function saveConfig(e) {{
          e.preventDefault();
          const fd = new FormData(e.target);
          const entries = Object.fromEntries(fd.entries());
          const res = await fetch('/api/config', {{ method: 'POST', headers: {{'Content-Type':'application/json'}}, body: JSON.stringify(entries) }});
          const data = await res.json();
          alert(data.message || '저장됨');
        }}

        async function saveNaverApp(e) {{
          e.preventDefault();
          const fd = new FormData(e.target);
          const entries = Object.fromEntries(fd.entries());
          const res = await fetch('/api/naver/credentials', {{ method: 'POST', headers: {{'Content-Type':'application/json'}}, body: JSON.stringify(entries) }});
          const data = await res.json();
          alert(data.message || '저장됨');
          await refreshNaverStatus();
        }}

        async function refreshNaverStatus() {{
          const res = await fetch('/api/naver/status');
          const data = await res.json();
          document.getElementById('naver_client_id').value = data.client_id || '';
          document.getElementById('naver_client_secret').value = data.client_secret ? '********' : '';
          document.getElementById('naver_redirect_uri').value = data.redirect_uri || 'http://localhost:8000/oauth/naver/callback';
          document.getElementById('naver_status').textContent = JSON.stringify(data, null, 2);
        }}

        refreshNaverStatus();
      </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


@app.post("/api/run")
def api_run(payload: Dict[str, Any]):
    count = payload.get("count")
    mode = payload.get("mode")
    dry_run = bool(payload.get("dry_run", False))
    res = run_once(config_path=_load_config_path(), count=int(count) if count else None, mode=mode, dry_run=dry_run)
    return JSONResponse(res)


@app.get("/api/naver/status")
def api_naver_status():
    app_info = get_naver_app()
    tok = get_naver_tokens()
    return JSONResponse({
        "client_id": app_info.get("client_id"),
        "client_secret": bool(app_info.get("client_secret")),
        "redirect_uri": app_info.get("redirect_uri", "http://localhost:8000/oauth/naver/callback"),
        "has_access_token": bool(tok.get("access_token")),
        "token_expires_in": tok.get("expires_in"),
    })


@app.post("/api/naver/credentials")
def api_naver_credentials(payload: Dict[str, Any]):
    cid = payload.get("client_id")
    cs = payload.get("client_secret")
    ru = payload.get("redirect_uri") or "http://localhost:8000/oauth/naver/callback"
    if not cid or not cs:
        return JSONResponse({"message": "client_id/secret 필요"}, status_code=400)
    save_naver_app(cid, cs, ru)
    return JSONResponse({"message": "저장되었습니다"})


# Simple in-memory state storage
_naver_state: Optional[str] = None


@app.get("/oauth/naver/start")
def oauth_naver_start():
    app_info = get_naver_app()
    cid = app_info.get("client_id")
    redirect_uri = app_info.get("redirect_uri") or "http://localhost:8000/oauth/naver/callback"
    if not cid:
        return JSONResponse({"message": "먼저 client_id/secret을 저장하세요"}, status_code=400)
    state = secrets.token_urlsafe(16)
    global _naver_state
    _naver_state = state
    params = {
        "response_type": "code",
        "client_id": cid,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    url = "https://nid.naver.com/oauth2.0/authorize?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


@app.get("/oauth/naver/callback")
def oauth_naver_callback(code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None, error_description: Optional[str] = None):
    if error:
        return HTMLResponse(f"<p>오류: {error} - {error_description}</p>")
    if not code:
        return HTMLResponse("<p>code 파라미터 누락</p>")
    global _naver_state
    if not state or state != _naver_state:
        return HTMLResponse("<p>state 불일치</p>")
    app_info = get_naver_app()
    cid = app_info.get("client_id")
    cs = app_info.get("client_secret")
    redirect_uri = app_info.get("redirect_uri")
    if not (cid and cs and redirect_uri):
        return HTMLResponse("<p>앱 자격증명이 설정되지 않았습니다.</p>")

    # Exchange code for token
    token_url = "https://nid.naver.com/oauth2.0/token"
    params = {
        "grant_type": "authorization_code",
        "client_id": cid,
        "client_secret": cs,
        "code": code,
        "state": state,
    }
    r = requests.get(token_url, params=params, timeout=20)
    if r.status_code >= 400:
        return HTMLResponse(f"<p>토큰 발급 실패: {r.status_code} {r.text}</p>")
    data = r.json()
    save_naver_tokens(data)
    _naver_state = None
    return HTMLResponse("<p>연결 완료! 페이지를 닫고 GUI로 돌아가세요.</p>")


@app.get("/api/config")
def api_get_config():
    cfg = read_config(_load_config_path())
    # Hide secrets if any accidentally present
    return JSONResponse(cfg)


@app.post("/api/config")
def api_set_config(payload: Dict[str, Any]):
    cfg = read_config(_load_config_path())

    def set_path(d: Dict[str, Any], path: str, value: Any):
        parts = path.split('.')
        cur = d
        for p in parts[:-1]:
            if p not in cur or not isinstance(cur[p], dict):
                cur[p] = {}
            cur = cur[p]
        cur[parts[-1]] = value

    for k, v in payload.items():
        # cast int fields
        if k.endswith('.daily_count'):
            try:
                v = int(v)
            except Exception:
                pass
        set_path(cfg, k, v)

    write_config(cfg, "config.yaml")
    return JSONResponse({"message": "저장되었습니다", "config": cfg})
