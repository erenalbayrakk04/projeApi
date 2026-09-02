"""
==============================================================================
Pydantic v2 Ürün Şemaları (Product Schemas / DTO - Data Transfer Objects)
==============================================================================
Bu dosya, Ürün (Product) domaini için veri doğrulama ve serileştirme modellerini
içerir. Kategoriler ile Çoka-Çok (Many-to-Many) ilişkiyi `category_ids` üzerinden
yönetir.
==============================================================================
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from .category import CategoryResponse


# ==============================================================================
# 1. ProductBase (Temel Ürün Şeması)
# ==============================================================================
class ProductBase(BaseModel):
    """
    Tüm ürün modellerinde ortak olan temel alanları tanımlayan şemadır.
    """

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Ürünün ticari adı (en az 2 karakter olmalıdır)",
        examples=["Kablosuz Mekanik Klavye"],
    )

    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Ürünün detaylı teknik ve genel açıklaması (opsiyonel)",
        examples=["RGB aydınlatmalı, Bluetooth ve Type-C bağlantılı mekanik klavye."],
    )

    price: float = Field(
        ...,
        gt=0,
        description="Ürünün birim satış fiyatı (0'dan büyük pozitif bir sayı olmalıdır)",
        examples=[1850.00],
    )

    stock: int = Field(
        ...,
        ge=0,
        description="Depodaki mevcut stok miktarı (0 veya daha büyük bir tam sayı)",
        examples=[40],
    )

    is_active: bool = Field(
        default=True,
        description="Ürünün aktif/satışta olup olmadığını belirten durum bayrağı",
        examples=[True],
    )


# ==============================================================================
# 2. ProductCreate (Yeni Ürün Ekleme Şeması - POST /products/)
# ==============================================================================
class ProductCreate(ProductBase):
    """
    Yeni ürün eklerken (HTTP POST) istemciden beklenen veri şemasıdır.
    Ürün en az 1 kategori ID'sine (Many-to-Many) bağlanmalıdır.
    """
    category_ids: List[int] = Field(
        ...,
        min_length=1,
        description="Ürünün ait olduğu kategori ID'lerinin listesi (en az 1 kategori ID'si gereklidir)",
        examples=[[1, 4, 5]],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Kablosuz Mekanik Klavye",
                "description": "RGB aydınlatmalı, Bluetooth ve Type-C bağlantılı mekanik klavye.",
                "price": 1850.00,
                "stock": 40,
                "category_ids": [1, 4, 5],
                "is_active": True,
            }
        }
    )


# ==============================================================================
# 3. ProductUpdate (Tam Güncelleme Şeması - PUT /products/{id})
# ==============================================================================
class ProductUpdate(ProductBase):
    """
    Ürünün tüm alanlarını ve kategori ilişkilerini baştan sona değiştirmek (PUT) için kullanılan şema.
    """
    category_ids: List[int] = Field(
        ...,
        min_length=1,
        description="Ürünün atanacağı güncel kategori ID'leri listesi",
        examples=[[1, 5]],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Kablosuz Mekanik Klavye V2",
                "description": "RGB aydınlatmalı ve manyetik bilek destekli yeni sürüm.",
                "price": 2100.00,
                "stock": 25,
                "category_ids": [1, 5],
                "is_active": True,
            }
        }
    )


# ==============================================================================
# 4. ProductPatch (Kısmi Güncelleme Şeması - PATCH /products/{id})
# ==============================================================================
class ProductPatch(BaseModel):
    """
    Ürünün yalnızca belirli alanlarını güncellemek (HTTP PATCH) için kullanılan şema.
    Tüm alanlar opsiyoneldir.
    """

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Güncellenecek yeni ürün adı",
        examples=["Ergonomik Dikey Mouse"],
    )

    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Güncellenecek yeni açıklama",
    )

    price: Optional[float] = Field(
        default=None,
        gt=0,
        description="Güncellenecek yeni fiyat",
        examples=[950.00],
    )

    stock: Optional[int] = Field(
        default=None,
        ge=0,
        description="Güncellenecek yeni stok miktarı",
        examples=[15],
    )

    category_ids: Optional[List[int]] = Field(
        default=None,
        min_length=1,
        description="Güncellenecek yeni kategori ID'leri listesi",
        examples=[[1, 3]],
    )

    is_active: Optional[bool] = Field(
        default=None,
        description="Güncellenecek yeni aktiflik durumu",
        examples=[False],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "price": 1699.90,
                "stock": 50,
                "category_ids": [1, 4]
            }
        }
    )


# ==============================================================================
# 5. ProductResponse (İstemciye Dönen Yanıt Şeması - Output Model)
# ==============================================================================
class ProductResponse(ProductBase):
    """
    API tarafından istemciye dönülen tam ürün nesnesini temsil eder.
    `category_ids` ve ilişkili `categories` (Kategori detayları) listesini içerir.
    """

    id: int = Field(
        ...,
        description="Otomatik oluşturulan benzersiz ürün ID'si",
        examples=[1],
    )

    category_ids: List[int] = Field(
        ...,
        description="Ürünün ait olduğu kategori ID'leri listesi",
        examples=[[1, 4, 5]],
    )

    categories: List[CategoryResponse] = Field(
        default_factory=list,
        description="Ürünün dahil olduğu kategorilerin detaylı nesne listesi",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Ürünün oluşturulma tarih ve saati (UTC)",
        examples=["2026-08-31T10:00:00Z"],
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Kablosuz Mekanik Klavye",
                "description": "RGB aydınlatmalı mekanik klavye.",
                "price": 1899.90,
                "stock": 35,
                "is_active": True,
                "category_ids": [1, 4, 5],
                "categories": [
                    {"id": 1, "name": "Elektronik", "description": "Teknoloji"},
                    {"id": 4, "name": "Aksesuar", "description": "Aparatlar"},
                    {"id": 5, "name": "Gaming", "description": "Oyuncu Ekipmanları"}
                ],
                "created_at": "2026-08-31T10:00:00Z",
            }
        },
    )
