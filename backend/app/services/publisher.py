from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from markdown import markdown as md_to_html
from app.models import Post, AffiliateMap
from app.services.naver import publish_blog_post


async def schedule_post(post_id: int, when: datetime, session: AsyncSession):
    post = await session.get(Post, post_id)
    if not post:
        return
    post.scheduled_at = when
    post.status = "scheduled"
    await session.commit()


async def publish_now(post_id: int, session: AsyncSession):
    post = await session.get(Post, post_id)
    if not post:
        return
    # Build HTML from Markdown and inject affiliate iframe if missing
    body_md = post.body_md or ""
    html = md_to_html(body_md)
    # If related affiliate HTML exists but not present in content, append
    if post.product_candidate_id:
        res = await session.execute(select(AffiliateMap).where(AffiliateMap.product_candidate_id == post.product_candidate_id))
        amap = res.scalars().first()
        if amap and amap.affiliate_html and (amap.affiliate_html not in body_md and amap.affiliate_html not in html):
            html = html.rstrip() + "\n" + amap.affiliate_html
    # publish to Naver
    post_id_naver = await publish_blog_post(post.title or "", html)
    post.naver_post_id = post_id_naver
    post.published_at = datetime.utcnow()
    post.status = "published" if post_id_naver else "failed"
    await session.commit()
