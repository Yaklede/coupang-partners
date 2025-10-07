from pydantic import BaseModel
from typing import Optional, List, Any, Dict


class KeywordCreate(BaseModel):
    text: str
    date_range: Optional[str] = None
    score: Optional[float] = None
    category: Optional[str] = None


class KeywordOut(BaseModel):
    id: int
    text: str
    date_range: Optional[str]
    score: Optional[float]
    category: Optional[str]
    status: str

    class Config:
        from_attributes = True


class ProductCandidateCreate(BaseModel):
    keyword_id: int
    title_guess: str
    brand: Optional[str] = None
    model: Optional[str] = None
    price_band: Optional[str] = None
    why: Optional[str] = None
    image_hint: Optional[str] = None
    dedupe_key: Optional[str] = None


class ProductCandidateOut(BaseModel):
    id: int
    keyword_id: int
    title_guess: str
    brand: Optional[str]
    model: Optional[str]
    price_band: Optional[str]
    why: Optional[str]
    image_hint: Optional[str]
    dedupe_key: Optional[str]
    status: str
    coupang_url: Optional[str] = None

    class Config:
        from_attributes = True


class AffiliateMapCreate(BaseModel):
    product_id: int
    url: str
    html: Optional[str] = None


class PostDraftCreate(BaseModel):
    product_id: int
    template_type: Optional[str] = "A"  # A/B/C/D/E
    template_input: Optional[Dict[str, Any]] = None


class PostPublish(BaseModel):
    post_id: int
    schedule: Optional[str] = None  # ISO datetime


class PostOut(BaseModel):
    id: int
    title: Optional[str]
    body_md: Optional[str]
    status: str
    scheduled_at: Optional[str]
    published_at: Optional[str]

    class Config:
        from_attributes = True


class PostDraftCompare(BaseModel):
    product_ids: List[int]
    template_input: Optional[Dict[str, Any]] = None


class MetricsQuery(BaseModel):
    from_: Optional[str] = None
    to: Optional[str] = None
