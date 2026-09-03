"""
==============================================================================
SQLAlchemy Kategori Deposu (Category Repository)
==============================================================================
Cosmic Python Repository Pattern standardında Kategori veri erişim deposu.
==============================================================================
"""

from typing import Any, Callable, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from interfaces.repositories import ICategoryRepository
from adapters.sqlalchemy.models import CategoryModel


class SqlAlchemyCategoryRepository(ICategoryRepository):
    """
    SQLAlchemy oturumu üzerinden kategori CRUD operasyonlarını yürüten depo.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory

    def add_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Yeni bir kategori kaydeder."""
        with self.session_factory() as session:
            cat = CategoryModel(
                name=category_data["name"].strip(),
                description=category_data.get("description"),
            )
            session.add(cat)
            session.commit()
            session.refresh(cat)
            return cat.to_dict()

    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """ID numarasına göre kategori getirir."""
        with self.session_factory() as session:
            cat = session.get(CategoryModel, category_id)
            return cat.to_dict() if cat else None

    def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """İsme göre kategori arar (büyük/küçük harf duyarsız)."""
        with self.session_factory() as session:
            cat = (
                session.query(CategoryModel)
                .filter(func.lower(CategoryModel.name) == func.lower(name.strip()))
                .first()
            )
            return cat.to_dict() if cat else None

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Tüm kategorileri ID sırasına göre listeler."""
        with self.session_factory() as session:
            cats = session.query(CategoryModel).order_by(CategoryModel.id.asc()).all()
            return [c.to_dict() for c in cats]

    def update_category(self, category_id: int, category_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mevcut bir kategoriyi günceller."""
        with self.session_factory() as session:
            cat = session.get(CategoryModel, category_id)
            if not cat:
                return None

            cat.name = category_data["name"].strip()
            if "description" in category_data:
                cat.description = category_data["description"]

            session.commit()
            session.refresh(cat)
            return cat.to_dict()

    def delete_category(self, category_id: int) -> bool:
        """Kategoriyi siler."""
        with self.session_factory() as session:
            cat = session.get(CategoryModel, category_id)
            if not cat:
                return False
            session.delete(cat)
            session.commit()
            return True
