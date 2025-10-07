import datetime as dt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Budget


TOKEN_PER_1K_COST = {
    "gpt-4o-mini": 0.15  # USD per 1K tokens approx (example)
}


async def add_usage(session: AsyncSession, tokens: int, usd: float | None = None):
    today = dt.date.today().isoformat()
    res = await session.execute(select(Budget).where(Budget.date == today))
    row = res.scalars().first()
    if not row:
        row = Budget(date=today, token_used=0, usd_spent=0.0)
        session.add(row)
    row.token_used += tokens
    if usd is None:
        # approximate
        row.usd_spent += (tokens / 1000.0) * TOKEN_PER_1K_COST.get("gpt-4o-mini", 0.15)
    else:
        row.usd_spent += usd
    await session.commit()


async def can_spend(session: AsyncSession, expected_usd: float) -> bool:
    today = dt.date.today().isoformat()
    res = await session.execute(select(Budget).where(Budget.date == today))
    row = res.scalars().first()
    spent = row.usd_spent if row else 0.0
    return spent + expected_usd <= (row.cap if row else 20.0)

