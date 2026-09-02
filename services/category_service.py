"""
==============================================================================
Kategori Servis Katmanı (Category Service - İş Mantığı Katmanı)
==============================================================================
Bu modül, kategori CRUD operasyonlarını, benzersiz isim kontrolünü ve
sayfalama işlemlerini yürütür.

SOLID Prensipleri:
- Dependency Inversion Principle (DIP): CategoryService somut SQLiteDatabase sınıfına
  değil, soyut ICategoryRepository arayüzüne bağımlıdır.
==============================================================================
"""

from typing import List, Optional
from fastapi import Depends
from interfaces.repositories import ICategoryRepository
from database import get_database
from schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)


class CategoryService:
    """
    Kategori işlemlerini yöneten iş mantığı sınıfı.
    """

    def __init__(self, repository: Optional[ICategoryRepository] = None) -> None:
        """
        Servisi soyut ICategoryRepository arayüzü ile başlatır (Dependency Injection).
        """
        self.db: ICategoryRepository = repository if repository is not None else get_database()

    def create_category(self, category_in: CategoryCreate) -> CategoryResponse:
        """
        Yeni bir kategori oluşturur.
        Aynı isimde kategori varsa ValueError fırlatır.
        """
        existing = self.db.get_category_by_name(category_in.name)
        if existing:
            raise ValueError(f"'{category_in.name}' isimli bir kategori zaten mevcut.")

        category_dict = category_in.model_dump()
        created_record = self.db.add_category(category_dict)
        return CategoryResponse.model_validate(created_record)

    def get_category_by_id(self, category_id: int) -> Optional[CategoryResponse]:
        """
        ID'ye göre kategori getirir.
        """
        record = self.db.get_category_by_id(category_id)
        if not record:
            return None
        return CategoryResponse.model_validate(record)

    def list_categories(self, skip: int = 0, limit: int = 10) -> List[CategoryResponse]:
        """
        Kategorileri sayfalama (skip/limit) desteğiyle listeler.
        """
        all_categories = self.db.get_all_categories()
        paginated = all_categories[skip : skip + limit]
        return [CategoryResponse.model_validate(item) for item in paginated]

    def update_category(self, category_id: int, category_in: CategoryUpdate) -> Optional[CategoryResponse]:
        """
        Mevcut bir kategoriyi günceller.
        İsim değiştiriliyorsa ve yeni isim başka bir kategoriye aitse hata fırlatır.
        """
        current_cat = self.db.get_category_by_id(category_id)
        if not current_cat:
            return None

        # İsim çakışması kontrolü
        existing_with_name = self.db.get_category_by_name(category_in.name)
        if existing_with_name and existing_with_name["id"] != category_id:
            raise ValueError(f"'{category_in.name}' isimli bir kategori zaten mevcut.")

        category_dict = category_in.model_dump()
        updated_record = self.db.update_category(category_id, category_dict)
        if not updated_record:
            return None
        return CategoryResponse.model_validate(updated_record)

    def delete_category(self, category_id: int) -> bool:
        """
        Kategoriyi siler.
        """
        return self.db.delete_category(category_id)


def get_category_service(
    repository: ICategoryRepository = Depends(get_database)
) -> CategoryService:
    """
    FastAPI Dependency Injection sağlayıcısı.
    Servise somut sınıf yerine ICategoryRepository soyut arayüzünü enjekte eder.
    """
    return CategoryService(repository=repository)
