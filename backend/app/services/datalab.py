import datetime as dt


async def fetch_trending_keywords() -> list[dict]:
    # NOTE: Real DataLab scraping often requires cookies/headers.
    # Stub returns sample keywords for demo and unit testing.
    today = dt.date.today().isoformat()
    sample = [
        {"text": "무선 청소기", "date_range": today, "score": 0.91, "category": "가전"},
        {"text": "게이밍 마우스", "date_range": today, "score": 0.87, "category": "디지털"},
        {"text": "공기청정기 필터", "date_range": today, "score": 0.82, "category": "생활"},
        {"text": "캠핑 의자", "date_range": today, "score": 0.79, "category": "레저"},
        {"text": "식기세척기 세제", "date_range": today, "score": 0.77, "category": "생활"},
    ]
    return sample

