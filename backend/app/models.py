import datetime as dt
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Boolean, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class Keyword(Base):
    __tablename__ = "keyword"
    __table_args__ = (
        UniqueConstraint("text", "date_range", name="uq_keyword_text_date"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(String(255), index=True)
    date_range: Mapped[str | None] = mapped_column(String(32), nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="new")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    candidates: Mapped[list["ProductCandidate"]] = relationship(back_populates="keyword")


class ProductCandidate(Base):
    __tablename__ = "product_candidate"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keyword.id", ondelete="CASCADE"))
    title_guess: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str | None] = mapped_column(String(128))
    model: Mapped[str | None] = mapped_column(String(128))
    price_band: Mapped[str | None] = mapped_column(String(64))
    why: Mapped[str | None] = mapped_column(Text)
    image_hint: Mapped[str | None] = mapped_column(String(255))
    dedupe_key: Mapped[str | None] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    keyword: Mapped[Keyword] = relationship(back_populates="candidates")
    affiliate_map: Mapped[list["AffiliateMap"]] = relationship(back_populates="candidate")


class AffiliateMap(Base):
    __tablename__ = "affiliate_map"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_candidate_id: Mapped[int] = mapped_column(ForeignKey("product_candidate.id", ondelete="CASCADE"))
    affiliate_url: Mapped[str] = mapped_column(Text)
    affiliate_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    mapped_by: Mapped[str | None] = mapped_column(String(64))
    mapped_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    candidate: Mapped[ProductCandidate] = relationship(back_populates="affiliate_map")


class Post(Base):
    __tablename__ = "post"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keyword.id", ondelete="SET NULL"), nullable=True)
    product_candidate_id: Mapped[int] = mapped_column(ForeignKey("product_candidate.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255))
    body_md: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[str | None] = mapped_column(Text)
    images: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    scheduled_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    naver_post_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    template_id: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class Metrics(Base):
    __tablename__ = "metrics"
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id", ondelete="CASCADE"), primary_key=True)
    impressions: Mapped[int | None] = mapped_column(Integer)
    clicks: Mapped[int | None] = mapped_column(Integer)
    ctr: Mapped[float | None] = mapped_column(Float)
    revenue: Mapped[float | None] = mapped_column(Float)
    template_id: Mapped[str | None] = mapped_column(String(16))


class Budget(Base):
    __tablename__ = "budget"
    date: Mapped[str] = mapped_column(String(10), primary_key=True)
    token_used: Mapped[int] = mapped_column(Integer, default=0)
    usd_spent: Mapped[float] = mapped_column(Float, default=0.0)
    cap: Mapped[float] = mapped_column(Float, default=20.0)


class NaverToken(Base):
    __tablename__ = "naver_token"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    access_token: Mapped[str | None] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text)
    token_type: Mapped[str | None] = mapped_column(String(32))
    expires_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class AppConfig(Base):
    __tablename__ = "app_config"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
