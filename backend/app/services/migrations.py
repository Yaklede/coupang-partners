from sqlalchemy import text
from app.db import engine


async def ensure_affiliate_html_column():
    async with engine.begin() as conn:
        res = await conn.exec_driver_sql("PRAGMA table_info('affiliate_map')")
        cols = [row[1] for row in res.fetchall()]
        if 'affiliate_html' not in cols:
            await conn.exec_driver_sql("ALTER TABLE affiliate_map ADD COLUMN affiliate_html TEXT")


async def ensure_post_meta_json_column():
    async with engine.begin() as conn:
        res = await conn.exec_driver_sql("PRAGMA table_info('post')")
        cols = [row[1] for row in res.fetchall()]
        if 'meta_json' not in cols:
            await conn.exec_driver_sql("ALTER TABLE post ADD COLUMN meta_json TEXT")
