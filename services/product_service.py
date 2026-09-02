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


class ProductService:
    """
    Ürün CRUD (Create, Read, Update, Delete) ve filtreleme işlemlerini
    gerçekleştiren iş mantığı servis sınıfı.
    """

    def __init__(self, repository: Optional[IProductRepository] = None) -> None:
        """
        Servisi soyut IProductRepository arayüzü ile başlatır (Dependency Injection).
        """
        self.db: IProductRepository = repository if repository is not None else get_database()

    def create_product(self, product_in: ProductCreate) -> ProductResponse:
        """
        Yeni bir ürün oluşturur ve kategori ilişkilerini kaydeder.
        """
        product_dict = product_in.model_dump()
        created_record = self.db.add(product_dict)
        return ProductResponse.model_validate(created_record)

    def get_product_by_id(self, product_id: int) -> Optional[ProductResponse]:
        """
        ID numarasına göre tek bir ürünü kategorileriyle birlikte getirir.
        """
        record = self.db.get_by_id(product_id)
        if not record:
            return None
        return ProductResponse.model_validate(record)

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
        Ürünleri filtre kriterlerine (kategori ismi, kategori ID'si, fiyat aralığı vb.)
        ve sayfalama parametrelerine göre süzer ve listeler.
        """
        all_products = self.db.get_all()
        filtered = all_products

        # 1. Kategori İsmine Göre Filtreleme (Ürünün kategorilerinden herhangi biri eşleşiyorsa)
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
        paginated_records = filtered[skip : skip + limit]

        return [ProductResponse.model_validate(item) for item in paginated_records]

    def update_product(
        self, product_id: int, product_in: ProductUpdate
    ) -> Optional[ProductResponse]:
        """
        Mevcut bir ürünü baştan sona (HTTP PUT) günceller.
        """
        product_dict = product_in.model_dump()
        updated_record = self.db.update(product_id, product_dict)
        if not updated_record:
            return None
        return ProductResponse.model_validate(updated_record)

    def patch_product(
        self, product_id: int, product_in: ProductPatch
    ) -> Optional[ProductResponse]:
        """
        Mevcut bir ürünü kısmi olarak (HTTP PATCH) günceller.
        """
        update_data = product_in.model_dump(exclude_unset=True)
        if not update_data:
            return self.get_product_by_id(product_id)

        updated_record = self.db.patch(product_id, update_data)
        if not updated_record:
            return None
        return ProductResponse.model_validate(updated_record)

    def delete_product(self, product_id: int) -> bool:
        """
        Belirtilen ID'ye sahip ürünü veritabanından siler.
        """
        return self.db.delete(product_id)


def get_product_service(
    repository: IProductRepository = Depends(get_database)
) -> ProductService:
    """
    FastAPI Dependency Injection sağlayıcısı.
    Servise somut sınıf yerine IProductRepository soyut arayüzünü enjekte eder.
    """
    return ProductService(repository=repository)
