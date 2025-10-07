from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    AI_PROVIDER: str = "gpt"  # 'gpt' | 'gemini'
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL_SMALL: str = "gpt-4o-mini"
    OPENAI_MODEL_WRITER: str = "gpt-4o-mini"
    OPENAI_MONTHLY_MAX_USD: float = 20.0
    OPENAI_HARD_STOP: bool = True

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL_SMALL: str = "gemini-1.5-flash"
    GEMINI_MODEL_WRITER: str = "gemini-1.5-pro"
    GEMINI_SAFETY: str = "low"  # 'default' | 'low' | 'none'

    NAVER_CLIENT_ID: str | None = None
    NAVER_CLIENT_SECRET: str | None = None
    NAVER_BLOG_ID: str | None = None
    NAVER_REDIRECT_URI: str | None = None

    RATE_LIMIT_PER_MIN: int = 10

    SLACK_WEBHOOK_URL: str | None = None

    POSTS_PER_DAY_MIN: int = 10
    POSTS_PER_DAY_MAX: int = 100
    POSTING_WINDOW_START: str = "09:00"
    POSTING_WINDOW_END: str = "23:30"
    ALLOW_MANUAL_REVIEW: bool = True
    LANGUAGE: str = "ko-KR"

    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    COUPANG_SCRAPE: bool = True
    COUPANG_SCRAPE_TIMEOUT: float = 12.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("POSTING_WINDOW_START", "POSTING_WINDOW_END")
    @classmethod
    def validate_time(cls, v: str) -> str:
        hh, mm = v.split(":")
        assert 0 <= int(hh) < 24 and 0 <= int(mm) < 60, "invalid HH:MM"
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
