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
from services.cache_service import CacheService, cache_service
from events.base import EventPublisher, event_bus
from events.domain_events import (
    CategoryCreatedEvent,
    CategoryUpdatedEvent,
    CategoryDeletedEvent,
)


class CategoryService:
    """
    Kategori işlemlerini yöneten, Redis Cache-Aside ve Observer Pattern destekli iş mantığı sınıfı.
    """

    def __init__(
        self,
        repository: Optional[ICategoryRepository] = None,
        cache: Optional[CacheService] = None,
        bus: Optional[EventPublisher] = None,
    ) -> None:
        """
        Servisi soyut bağımlılıklar ile başlatır (Dependency Injection).
        """
        self.db: ICategoryRepository = repository if repository is not None else get_database()
        self.cache: CacheService = cache if cache is not None else cache_service
        self.bus: EventPublisher = bus if bus is not None else event_bus

    def create_category(self, category_in: CategoryCreate) -> CategoryResponse:
        """
        Yeni bir kategori oluşturur ve CategoryCreatedEvent yayınlar.
        Aynı isimde kategori varsa ValueError fırlatır.
        """
        existing = self.db.get_category_by_name(category_in.name)
        if existing:
            raise ValueError(f"'{category_in.name}' isimli bir kategori zaten mevcut.")

        category_dict = category_in.model_dump()
        created_record = self.db.add_category(category_dict)
        response = CategoryResponse.model_validate(created_record)

        # Observer Pattern: Olayı yayınla
        self.bus.publish(
            CategoryCreatedEvent(
                category_id=response.id,
                name=response.name,
                payload=response.model_dump(),
            )
        )

        return response

    def get_category_by_id(self, category_id: int) -> Optional[CategoryResponse]:
        """
        ID'ye göre kategoriyi Cache-Aside stratejisiyle getirir.
        """
        cache_key = f"categories:item:{category_id}"

        def fetch_from_db():
            record = self.db.get_category_by_id(category_id)
            if not record:
                return None
            return record

        cached_dict = self.cache.get_or_set(cache_key, fetch_from_db, ttl_seconds=300)
        if not cached_dict:
            return None
        return CategoryResponse.model_validate(cached_dict)

    def list_categories(self, skip: int = 0, limit: int = 10) -> List[CategoryResponse]:
        """
        Kategorileri sayfalama (skip/limit) desteği ve Cache-Aside ile listeler.
        """
        cache_key = f"categories:list:skip={skip}:limit={limit}"

        def fetch_from_db():
            all_categories = self.db.get_all_categories()
            return all_categories[skip : skip + limit]

        cached_records = self.cache.get_or_set(cache_key, fetch_from_db, ttl_seconds=300)
        return [CategoryResponse.model_validate(item) for item in cached_records]

    def update_category(self, category_id: int, category_in: CategoryUpdate) -> Optional[CategoryResponse]:
        """
        Mevcut bir kategoriyi günceller ve CategoryUpdatedEvent yayınlar.
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

        response = CategoryResponse.model_validate(updated_record)

        # Observer Pattern: Olayı yayınla
        self.bus.publish(
            CategoryUpdatedEvent(
                category_id=category_id,
                name=response.name,
                payload=response.model_dump(),
            )
        )

        return response

    def delete_category(self, category_id: int) -> bool:
        """
        Kategoriyi siler ve CategoryDeletedEvent yayınlar.
        """
        success = self.db.delete_category(category_id)
        if success:
            # Observer Pattern: Olayı yayınla
            self.bus.publish(CategoryDeletedEvent(category_id=category_id))
        return success


def get_category_service(
    repository: ICategoryRepository = Depends(get_database)
) -> CategoryService:
    """
    FastAPI Dependency Injection sağlayıcısı.
    Servise somut sınıf yerine ICategoryRepository soyut arayüzünü enjekte eder.
    """
    return CategoryService(repository=repository)

