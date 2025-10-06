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
from ..aff_store import put_affiliate, all_affiliates
from ..orchestrator import run_once
from ..trends import generate_trending_keywords
from ..recommend import recommend_products_from_keywords
from ..trends.naver_datalab import trending_seeds_from_datalab, datalab_trend_context
from ..miner import select_coupang_miner
from ..store import mark_posted, posted_set
from ..aff_store import get_affiliate


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
        <h3>상품 찾기</h3>
        <p>트렌드(네이버 DataLab + OpenAI) 기반으로 아직 게시하지 않은 상품 10개를 자동으로 찾습니다.</p>
        <div style='display:flex; gap:.5rem; align-items:center;'>
          <button onclick="discoverProducts()">상품 10개 찾기</button>
          <input id='kw' placeholder='키워드 직접 입력 (예: 가습기)' style='flex:1;'/>
          <button onclick="discoverByKeyword()">이 키워드로 찾기</button>
        </div>
        <div id='discover_list' style='margin-top:1rem'></div>
        <div style='margin-top:1rem'>
          <button onclick='generateSelected()'>선택한 상품으로 글 생성</button>
        </div>
      </div>

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
        <div style='margin-top:8px;'>
          <button onclick='copyOutput()'>복사</button>
          <button onclick='markSelectedPosted()'>선택 상품 게시 완료로 표시</button>
        </div>
      </div>

      <div class='card'>
        <h3>제휴 링크(포털) 수동 등록</h3>
        <p>API를 아직 사용할 수 없는 경우, 쿠팡 파트너스 포털에서 생성한 제휴 링크를 여기 등록하세요. 수집된 원본 상품 URL과 매핑되어 자동으로 사용됩니다.</p>
        <p>
          파트너스 포털: <a href='https://partners.coupang.com/#affiliate/ws' target='_blank'>https://partners.coupang.com/#affiliate/ws</a>
        </p>
        <form onsubmit="saveAffiliate(event)">
          <label>원본 상품 URL</label>
          <input name='raw_url' placeholder='https://www.coupang.com/...'/>
          <label>제휴 링크 URL</label>
          <input name='affiliate_url' placeholder='https://link.coupang.com/...'/>
          <div style='margin-top:1rem'>
            <button type='submit'>매핑 저장</button>
          </div>
        </form>
        <details style='margin-top:1rem'>
          <summary>등록된 매핑 보기</summary>
          <pre id='aff_map'>로딩 중…</pre>
        </details>
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

        function productRow(item) {{
          const aff = item.affiliate_url || '';
          return `
            <div style='border:1px solid #eee;padding:.5rem;border-radius:6px;margin:.5rem 0;'>
              <label><input type='checkbox' class='sel' value='${{encodeURIComponent(item.url||'')}}'/></label>
              <strong>${{item.title||''}}</strong>
              <div>
                <a href='${{item.url||'#'}}' target='_blank'>쿠팡 검색</a>
                ${{item.query?(' · 검색어: '+item.query):''}}
              </div>
              ${{item.reason?`<div style='color:#666'>추천 사유: ${item.reason}</div>`:''}}
              <div>
                제휴링크: <input class='aff' data-raw='${{encodeURIComponent(item.url||'')}}' value='${{aff}}' placeholder='https://link.coupang.com/...'/>
                <button onclick='saveAff("${{encodeURIComponent(item.url||'')}}")'>저장</button>
              </div>
            </div>`;
        }}

        async function discoverProducts() {{
          const res = await fetch('/api/products/discover?limit=10');
          const data = await res.json();
          const html = data.items.map(productRow).join('');
          document.getElementById('discover_list').innerHTML = html || '결과 없음';
        }}

        async function discoverByKeyword() {{
          const kw = document.getElementById('kw').value.trim();
          if (!kw) {{ alert('키워드를 입력하세요'); return; }}
          const res = await fetch(`/api/products/discover?limit=10&kw=${{encodeURIComponent(kw)}}`);
          const data = await res.json();
          const html = data.items.map(productRow).join('');
          document.getElementById('discover_list').innerHTML = html || '결과 없음';
        }}

        async function saveAff(rawEnc) {{
          const raw = decodeURIComponent(rawEnc);
          const input = document.querySelector(`input.aff[data-raw="${{rawEnc}}"]`);
          const aff = input.value.trim();
          const res = await fetch('/api/affiliate', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{raw_url:raw, affiliate_url:aff}})}});
          const data = await res.json();
          alert(data.message || '저장됨');
        }}

        async function generateSelected() {{
          const checks = Array.from(document.querySelectorAll('#discover_list input.sel:checked'));
          if (checks.length === 0) {{ alert('선택된 상품이 없습니다'); return; }}
          const raws = checks.map(c => decodeURIComponent(c.value));
          const rows = Array.from(document.querySelectorAll('#discover_list .aff'));
          const affMap = Object.fromEntries(rows.map(r=>[decodeURIComponent(r.getAttribute('data-raw')), r.value.trim()]));
          const payload = {{ products: raws.map(url => ({{ url, affiliate_url: affMap[url]||null }})) }};
          const res = await fetch('/api/generate', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify(payload)}});
          const data = await res.json();
          document.getElementById('out').textContent = data.html || JSON.stringify(data, null, 2);
        }}

        async function markSelectedPosted() {{
          const checks = Array.from(document.querySelectorAll('#discover_list input.sel:checked'));
          if (checks.length === 0) {{ alert('선택 없음'); return; }}
          const raws = checks.map(c => decodeURIComponent(c.value));
          await fetch('/api/posted', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{urls: raws}})}});
          alert('표시 완료');
        }}

        async function copyOutput() {{
          const txt = document.getElementById('out').textContent;
          try {{ await navigator.clipboard.writeText(txt); alert('복사 완료'); }} catch(e) {{ alert('복사 실패: '+e); }}
        }}

        async function saveAffiliate(e) {{
          e.preventDefault();
          const fd = new FormData(e.target);
          const body = Object.fromEntries(fd.entries());
          const res = await fetch('/api/affiliate', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify(body) }});
          const data = await res.json();
          alert(data.message || '저장됨');
          await refreshAffiliates();
        }}

        async function refreshAffiliates() {{
          const res = await fetch('/api/affiliate');
          const data = await res.json();
          document.getElementById('aff_map').textContent = JSON.stringify(data, null, 2);
        }}

        refreshAffiliates();

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


@app.get("/api/products/discover")
def api_products_discover(limit: int = 10, kw: Optional[str] = None):
    s = load_settings(_load_config_path())
    if kw:
        seeds = [kw]
    else:
        # Use DataLab to pick trending seeds from configured seed categories
        seeds = trending_seeds_from_datalab(s.keywords.seed_categories or ["가전","주방","리빙","디지털"], topk=5)
    trend_ctx = datalab_trend_context(seeds, days=30)
    llm_status = "ok"
    llm_error = None
    try:
        recs = recommend_products_from_keywords(s.providers.openai_model, seeds, count=limit, trend_context=trend_ctx)
    except Exception as e:
        llm_status = "error"
        llm_error = str(e)
        recs = []
    seen = set()
    posted = posted_set()
    items = []
    import urllib.parse as _uq
    for r in recs:
        name = r.get("name")
        if not name:
            continue
        sq = r.get("search_query") or name
        url = f"https://www.coupang.com/np/search?q={_uq.quote(sq)}"
        if url in seen or url in posted:
            continue
        seen.add(url)
        items.append({
            "id": name,
            "title": name,
            "price": None,
            "rating": None,
            "url": url,
            "affiliate_url": get_affiliate(url) or None,
            "reason": r.get("reason") or "trend-based",
            "query": sq,
        })
        if len(items) >= limit:
            break
    return JSONResponse({
        "items": items,
        "keywords": seeds,
        "source": "naver_datalab+openai",
        "meta": {"llm_status": llm_status, "llm_error": llm_error, "trend": trend_ctx},
    })


@app.post("/api/generate")
def api_generate(payload: Dict[str, Any]):
    # payload: { products: [{ url, affiliate_url? }] }
    products = payload.get("products") or []
    if not products:
        return JSONResponse({"message": "products 비어있음"}, status_code=400)
    # Build a roundup HTML purely from provided names + links (no crawling)
    s = load_settings(_load_config_path())
    from ..writer import inject_disclosure
    from ..writer import render_minimal_html
    from ..writer import chat_text, WRITER_SYSTEM
    import json as _json

    collected = []
    for it in products:
        name = it.get("title") or it.get("name") or "상품"
        url = it.get("url")
        if not url:
            # generate link from name
            import urllib.parse as _uq
            url = f"https://www.coupang.com/np/search?q={_uq.quote(name)}"
        collected.append({
            "title": name,
            "url": url,
            "deeplink": it.get("affiliate_url") or get_affiliate(url) or url,
            "price": None,
            "rating": None,
            "specs": {},
        })

    # Ask LLM to produce a roundup HTML from the list
    try:
        sys = (
            "역할: 한국어 쇼핑 블로거. 입력 제품 목록으로 네이버 블로그용 라운드업 글을 작성합니다.\n"
            "규칙: 각 제품마다 2~3문장 미니리뷰 + 장단점 1~2개 + 사용팁 1개. 과장/의학적 표현 금지.\n"
            "출력: 한국어 HTML, 소제목 <h3>, 굵게 <strong>, CTA는 제공된 deeplink 사용."
        )
        user = _json.dumps({"products": collected}, ensure_ascii=False)
        html = chat_text(model=s.providers.openai_model, system=sys, user=user, temperature=0.6, max_tokens=1600)
    except Exception:
        # fallback: concatenate minimal blocks
        block = []
        for c in collected:
            block.append(render_minimal_html(c))
        html = "\n".join(block)

    return JSONResponse({"html": inject_disclosure(html)})


@app.post("/api/posted")
def api_mark_posted(payload: Dict[str, Any]):
    urls = payload.get("urls") or []
    if not urls:
        return JSONResponse({"message": "urls 비어있음"}, status_code=400)
    mark_posted(urls)
    return JSONResponse({"message": "저장되었습니다"})


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


@app.get("/api/affiliate")
def api_get_affiliates():
    return JSONResponse(all_affiliates())


@app.post("/api/affiliate")
def api_put_affiliate(payload: Dict[str, Any]):
    raw = payload.get("raw_url")
    aff = payload.get("affiliate_url")
    if not raw or not aff:
        return JSONResponse({"message": "raw_url/affiliate_url 필요"}, status_code=400)
    put_affiliate(raw, aff)
    return JSONResponse({"message": "저장되었습니다"})
