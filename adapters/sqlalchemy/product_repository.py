"""
==============================================================================
SQLAlchemy Ürün Deposu (Product Repository)
==============================================================================
Cosmic Python Repository Pattern standardında Ürün veri erişim deposu.
==============================================================================
"""

from typing import Any, Callable, Dict, List, Optional
from sqlalchemy.orm import Session

from interfaces.repositories import IProductRepository
from adapters.sqlalchemy.models import CategoryModel, ProductModel


class SqlAlchemyProductRepository(IProductRepository):
    """
    SQLAlchemy oturumu üzerinden Ürün CRUD operasyonlarını yürüten depo.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory

    def add(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Yeni bir ürün kaydeder ve kategori ilişkilerini bağlar."""
        with self.session_factory() as session:
            category_ids = product_data.get("category_ids", [])
            categories = []
            if category_ids:
                categories = (
                    session.query(CategoryModel)
                    .filter(CategoryModel.id.in_(category_ids))
                    .all()
                )
                if len(categories) != len(set(category_ids)):
                    found_ids = {c.id for c in categories}
                    missing = set(category_ids) - found_ids
                    raise ValueError(f"Belirtilen kategoriler bulunamadı: {missing}")

            product = ProductModel(
                name=product_data["name"].strip(),
                description=product_data.get("description"),
                price=product_data["price"],
                stock=product_data["stock"],
                is_active=product_data.get("is_active", True),
                categories=categories,
            )
            session.add(product)
            session.commit()
            session.refresh(product)
            return product.to_dict()

    def get_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """ID numarasına göre ürünü kategorileriyle birlikte getirir."""
        with self.session_factory() as session:
            product = session.get(ProductModel, product_id)
            return product.to_dict() if product else None

    def get_all(self) -> List[Dict[str, Any]]:
        """Tüm ürünleri listeler."""
        with self.session_factory() as session:
            products = (
                session.query(ProductModel)
                .order_by(ProductModel.id.asc())
                .all()
            )
            return [p.to_dict() for p in products]

    def update(self, product_id: int, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mevcut bir ürünü baştan sona (PUT) günceller."""
        with self.session_factory() as session:
            product = session.get(ProductModel, product_id)
            if not product:
                return None

            category_ids = product_data.get("category_ids", [])
            categories = []
            if category_ids:
                categories = (
                    session.query(CategoryModel)
                    .filter(CategoryModel.id.in_(category_ids))
                    .all()
                )
                if len(categories) != len(set(category_ids)):
                    found_ids = {c.id for c in categories}
                    missing = set(category_ids) - found_ids
                    raise ValueError(f"Belirtilen kategoriler bulunamadı: {missing}")

            product.name = product_data["name"].strip()
            product.description = product_data.get("description")
            product.price = product_data["price"]
            product.stock = product_data["stock"]
            product.is_active = product_data.get("is_active", True)
            product.categories = categories

            session.commit()
            session.refresh(product)
            return product.to_dict()

    def patch(self, product_id: int, partial_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mevcut bir ürünü kısmi olarak (PATCH) günceller."""
        with self.session_factory() as session:
            product = session.get(ProductModel, product_id)
            if not product:
                return None

            if "name" in partial_data:
                product.name = partial_data["name"].strip()
            if "description" in partial_data:
                product.description = partial_data["description"]
            if "price" in partial_data:
                product.price = partial_data["price"]
            if "stock" in partial_data:
                product.stock = partial_data["stock"]
            if "is_active" in partial_data:
                product.is_active = partial_data["is_active"]
            if "category_ids" in partial_data:
                category_ids = partial_data["category_ids"]
                categories = (
                    session.query(CategoryModel)
                    .filter(CategoryModel.id.in_(category_ids))
                    .all()
                )
                if len(categories) != len(set(category_ids)):
                    found_ids = {c.id for c in categories}
                    missing = set(category_ids) - found_ids
                    raise ValueError(f"Belirtilen kategoriler bulunamadı: {missing}")
                product.categories = categories

            session.commit()
            session.refresh(product)
            return product.to_dict()

    def delete(self, product_id: int) -> bool:
        """Ürünü siler."""
        with self.session_factory() as session:
            product = session.get(ProductModel, product_id)
            if not product:
                return False
            session.delete(product)
            session.commit()
            return True
