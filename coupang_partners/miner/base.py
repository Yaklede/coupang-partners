from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..models import Product


class ProductMiner(ABC):
    @abstractmethod
    def search_products(self, keyword: str, limit: int = 10) -> List[Product]:
        ...

    @abstractmethod
    def enrich_product(self, product: Product) -> Product:
        ...

