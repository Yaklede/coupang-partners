from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import List, Dict, Optional


@dataclass_json
@dataclass
class Product:
    id: str
    title: str
    brand: Optional[str] = None
    category: List[str] = field(default_factory=list)
    price: Optional[float] = None
    sale_rate: Optional[float] = None
    rating: Optional[float] = None
    review_cnt: Optional[int] = None
    specs: Dict[str, str] = field(default_factory=dict)
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    best_for: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    deeplink: Optional[str] = None
    url: Optional[str] = None


@dataclass_json
@dataclass
class ProductSearchResult:
    keyword: str
    items: List[Product] = field(default_factory=list)

