"""
==============================================================================
Pydantic v2 Kategori Şemaları (Category Schemas / DTO)
==============================================================================
Bu modül, Kategori domaini için veri doğrulama ve serileştirme modellerini içerir.
==============================================================================
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):
    """
    Tüm Kategori şemalarının miras aldığı temel sınıf.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Kategori adı (en az 2 karakter olmalıdır)",
        examples=["Elektronik"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Kategori açıklaması (opsiyonel)",
        examples=["Elektronik aletler, bilgisayar ve çevre birimleri."],
    )


class CategoryCreate(CategoryBase):
    """
    Yeni kategori oluşturma (POST /categories/) için kullanılan şema.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Elektronik",
                "description": "Bilgisayar, monitör, klavye ve elektronik aksesuarlar.",
            }
        }
    )


class CategoryUpdate(CategoryBase):
    """
    Kategori güncelleme (PUT /categories/{id}) için kullanılan şema.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Tüketici Elektroniği",
                "description": "Güncellenmiş elektronik kategori açıklaması.",
            }
        }
    )


class CategoryResponse(CategoryBase):
    """
    API tarafından istemciye dönülen Kategori yanıt nesnesi.
    """
    id: int = Field(..., description="Kategorinin benzersiz ID'si", examples=[1])
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Kategorinin oluşturulma zamanı (UTC)",
        examples=["2026-08-31T10:00:00Z"],
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Elektronik",
                "description": "Bilgisayar, monitör, klavye ve elektronik aksesuarlar.",
                "created_at": "2026-08-31T10:00:00Z",
            }
        },
    )
