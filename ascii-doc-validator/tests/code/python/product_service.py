from typing import List
from models import Product

class ProductService:
    """Сервис управления продуктами."""

    def __init__(self):
        self.products: List[Product] = []

    def add_product(self, product: Product) -> None:
        self.products.append(product)

    def remove_product(self, sku: str) -> bool:
        original_len = len(self.products)
        self.products = [p for p in self.products if p.sku != sku]
        return len(self.products) < original_len