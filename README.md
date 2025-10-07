## Coupang Partners — Naver Blog Auto Posting (Web UI)

A full‑stack web app implementing the pipeline in `AGENTS.md` with a GUI for HITL (human‑in‑the‑loop) mapping and publishing.

### Stack
- Backend: FastAPI, SQLAlchemy/SQLite, Pydantic, httpx, python‑dotenv
- Frontend: Vite + React + TypeScript

### Quick Start
1) Backend
```
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill keys
uvicorn app.main:app --reload
```

2) Frontend
```
cd frontend
pnpm install  # or npm/yarn
pnpm dev
```

Backend runs on http://localhost:8000, Frontend on http://localhost:5173.

### Docker (one command)
Build and start both backend and frontend (served by Nginx, proxying `/api`):
```
docker compose up --build
```

- Web UI: http://localhost:8080
- API (optional direct): http://localhost:8000

Notes:
- Copy `backend/.env.example` to `backend/.env` and fill secrets before running.
- When using Docker, set your Naver OAuth redirect URI to `http://localhost:8080/api/auth/naver/callback` in the Naver Developers console. The proxy passes it to the API.

### Frontend API base URL
- The frontend auto-detects the API base URL:
  - If `VITE_API_BASE_URL` is set, uses that.
  - If the page has a non-default port (e.g., 5173/8080), it calls `/api` (proxied in dev and Docker).
  - If running on port 80/443, it defaults to `http://localhost:8000/api` to include the API port.
- To override explicitly, create `frontend/.env.development` or `.env.production` with:
```
VITE_API_BASE_URL=http://localhost:8000/api
```

### Environment
Create `backend/.env`:
```
AI_PROVIDER=gpt   # or gemini
OPENAI_API_KEY=sk-...
OPENAI_MODEL_SMALL=gpt-4o-mini
OPENAI_MODEL_WRITER=gpt-4o-mini
OPENAI_MONTHLY_MAX_USD=20
OPENAI_HARD_STOP=true

GEMINI_API_KEY=
GEMINI_MODEL_SMALL=gemini-1.5-flash
GEMINI_MODEL_WRITER=gemini-1.5-pro

NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
NAVER_BLOG_ID=
NAVER_REDIRECT_URI=http://localhost:8000/api/auth/naver/callback

RATE_LIMIT_PER_MIN=10

SLACK_WEBHOOK_URL=

POSTS_PER_DAY_MIN=10
POSTS_PER_DAY_MAX=100
POSTING_WINDOW_START=09:00
POSTING_WINDOW_END=23:30
ALLOW_MANUAL_REVIEW=true
LANGUAGE=ko-KR
```

### AI Provider selection
- Switch provider and models in the web UI (Settings → AI 모델 설정). Keys must be provided via `backend/.env`.
- Diagnostics (Settings → AI 연결 확인) verifies current provider configuration and connectivity.

### Notes
- DataLab crawling is pluggable; default uses a heuristic/stub when scraping is blocked.
- Naver OAuth2 flow and publish API are implemented as providers; real posting requires valid keys + consent.
- BudgetGuardian counts prompt/response sizes to approximate cost.
