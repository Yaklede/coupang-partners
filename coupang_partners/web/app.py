from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from ..config import load_settings
from ..config_store import read_config, write_config
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
