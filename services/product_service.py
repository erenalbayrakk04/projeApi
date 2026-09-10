"""
==============================================================================
Ürün Servis Katmanı (Product Service - İş Mantığı Katmanı)
==============================================================================
Bu modül, ürün yönetimi ile ilgili tüm iş kurallarını (business logic), filtreleme,
sayfalama ve veri dönüşümü işlemlerini yürütür.

SOLID Prensipleri:
- Dependency Inversion Principle (DIP): ProductService somut SQLiteDatabase sınıfına
  değil, soyut IProductRepository arayüzüne bağımlıdır.
==============================================================================
"""

from typing import List, Optional
from fastapi import Depends
from interfaces.repositories import IProductRepository
from database import get_database
from schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductPatch,
    ProductResponse,
)
from services.cache_service import CacheService, cache_service
from events.base import EventPublisher, event_bus
from events.domain_events import (
    ProductCreatedEvent,
    ProductUpdatedEvent,
    ProductDeletedEvent,
)


class ProductService:
    """
    Ürün CRUD (Create, Read, Update, Delete) ve filtreleme işlemlerini
    gerçekleştiren, Redis Cache-Aside ve Observer Pattern destekli iş mantığı servis sınıfı.
    """

    def __init__(
        self,
        repository: Optional[IProductRepository] = None,
        cache: Optional[CacheService] = None,
        bus: Optional[EventPublisher] = None,
    ) -> None:
        """
        Servisi soyut bağımlılıklar ile başlatır (Dependency Injection).
        """
        self.db: IProductRepository = repository if repository is not None else get_database()
        self.cache: CacheService = cache if cache is not None else cache_service
        self.bus: EventPublisher = bus if bus is not None else event_bus

    def create_product(self, product_in: ProductCreate) -> ProductResponse:
        """
        Yeni bir ürün oluşturur, kategori ilişkilerini kaydeder ve ProductCreatedEvent yayınlar.
        """
        product_dict = product_in.model_dump()
        created_record = self.db.add(product_dict)
        response = ProductResponse.model_validate(created_record)

        # Observer Pattern: Olayı yayınla
        self.bus.publish(
            ProductCreatedEvent(
                product_id=response.id,
                name=response.name,
                price=response.price,
                stock=response.stock,
                category_ids=response.category_ids,
                payload=response.model_dump(),
            )
        )

        return response

    def get_product_by_id(self, product_id: int) -> Optional[ProductResponse]:
        """
        ID numarasına göre tek bir ürünü Cache-Aside stratejisiyle getirir.
        """
        cache_key = f"products:item:{product_id}"

        def fetch_from_db():
            record = self.db.get_by_id(product_id)
            if not record:
                return None
            return record

        cached_dict = self.cache.get_or_set(cache_key, fetch_from_db, ttl_seconds=120)
        if not cached_dict:
            return None

        return ProductResponse.model_validate(cached_dict)

    def get_products(
        self,
        category: Optional[str] = None,
        category_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> List[ProductResponse]:
        """
        Ürünleri filtre kriterlerine ve sayfalama parametrelerine göre
        Redis Cache-Aside stratejisiyle süzer ve listeler.
        """
        cache_key = (
            f"products:list:cat={category}:cat_id={category_id}:"
            f"min={min_price}:max={max_price}:active={is_active}:skip={skip}:limit={limit}"
        )

        def fetch_filtered_from_db() -> List[dict]:
            all_products = self.db.get_all()
            filtered = all_products

            # 1. Kategori İsmine Göre Filtreleme
            if category is not None:
                clean_cat = category.strip().lower()
                filtered = [
                    p for p in filtered
                    if any(c["name"].strip().lower() == clean_cat for c in p.get("categories", []))
                ]

            # 2. Kategori ID'sine Göre Filtreleme
            if category_id is not None:
                filtered = [
                    p for p in filtered
                    if category_id in p.get("category_ids", [])
                ]

            # 3. Minimum Fiyata Göre Filtreleme
            if min_price is not None:
                filtered = [
                    p for p in filtered
                    if p.get("price", 0.0) >= min_price
                ]

            # 4. Maksimum Fiyata Göre Filtreleme
            if max_price is not None:
                filtered = [
                    p for p in filtered
                    if p.get("price", 0.0) <= max_price
                ]

            # 5. Aktiflik Durumuna Göre Filtreleme
            if is_active is not None:
                filtered = [
                    p for p in filtered
                    if p.get("is_active") == is_active
                ]

            # 6. Sayfalama (Pagination)
            paginated = filtered[skip : skip + limit]
            return paginated

        cached_records = self.cache.get_or_set(cache_key, fetch_filtered_from_db, ttl_seconds=60)
        return [ProductResponse.model_validate(item) for item in cached_records]

    def update_product(
        self, product_id: int, product_in: ProductUpdate
    ) -> Optional[ProductResponse]:
        """
        Mevcut bir ürünü baştan sona (HTTP PUT) günceller ve ProductUpdatedEvent yayınlar.
        """
        product_dict = product_in.model_dump()
        updated_record = self.db.update(product_id, product_dict)
        if not updated_record:
            return None

        response = ProductResponse.model_validate(updated_record)

        # Observer Pattern: Olayı yayınla
        self.bus.publish(
            ProductUpdatedEvent(
                product_id=product_id,
                updated_fields=product_dict,
                payload=response.model_dump(),
            )
        )

        return response

    def patch_product(
        self, product_id: int, product_in: ProductPatch
    ) -> Optional[ProductResponse]:
        """
        Mevcut bir ürünü kısmi olarak (HTTP PATCH) günceller ve ProductUpdatedEvent yayınlar.
        """
        update_data = product_in.model_dump(exclude_unset=True)
        if not update_data:
            return self.get_product_by_id(product_id)

        updated_record = self.db.patch(product_id, update_data)
        if not updated_record:
            return None

        response = ProductResponse.model_validate(updated_record)

        # Observer Pattern: Olayı yayınla
        self.bus.publish(
            ProductUpdatedEvent(
                product_id=product_id,
                updated_fields=update_data,
                payload=response.model_dump(),
            )
        )

        return response

    def delete_product(self, product_id: int) -> bool:
        """
        Belirtilen ID'ye sahip ürünü siler ve ProductDeletedEvent yayınlar.
        """
        success = self.db.delete(product_id)
        if success:
            # Observer Pattern: Olayı yayınla
            self.bus.publish(ProductDeletedEvent(product_id=product_id))
        return success


def get_product_service(
    repository: IProductRepository = Depends(get_database)
) -> ProductService:
    """
    FastAPI Dependency Injection sağlayıcısı.
    """
    return ProductService(repository=repository)

