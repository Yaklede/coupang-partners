from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.settings import settings
from app.routers import keywords, products, affiliate, posts, metrics, auth
from app.routers import admin
from app.routers import diagnostics
from app.services.scheduler import init_scheduler
from app.db import engine, Base
from app.services.migrations import ensure_affiliate_html_column, ensure_post_meta_json_column


app = FastAPI(title="Coupang Partners Orchestrator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(keywords.router, prefix="/api/keywords", tags=["keywords"]) 
app.include_router(products.router, prefix="/api/products", tags=["products"]) 
app.include_router(affiliate.router, prefix="/api/affiliate", tags=["affiliate"]) 
app.include_router(posts.router, prefix="/api/posts", tags=["posts"]) 
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"]) 
app.include_router(admin.router, prefix="/api/admin", tags=["admin"]) 
app.include_router(diagnostics.router, prefix="/api/diagnostics", tags=["diagnostics"]) 


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_affiliate_html_column()
    await ensure_post_meta_json_column()
    await init_scheduler(app)


@app.get("/api/health")
def health():
    return {"ok": True}
