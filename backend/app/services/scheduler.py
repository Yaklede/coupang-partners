from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from sqlalchemy import select
from datetime import datetime, timezone
from app.db import AsyncSessionLocal
from app.models import Post
from app.services.publisher import publish_now


async def _tick_publish_due():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Post).where(Post.status == "scheduled"))
        now = datetime.now(timezone.utc)
        for post in res.scalars():
            if post.scheduled_at and post.scheduled_at <= now.replace(tzinfo=None):
                await publish_now(post.id, session)


async def init_scheduler(app: FastAPI):
    sched = AsyncIOScheduler()
    sched.add_job(_tick_publish_due, IntervalTrigger(seconds=30))
    sched.start()
    app.state.scheduler = sched

