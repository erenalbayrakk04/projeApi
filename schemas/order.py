"""
==============================================================================
Pydantic v2 Sipariş Şemaları (Order Schemas / DTO)
==============================================================================
Bu modül, Sipariş (Order) ve Sipariş Kalemleri (OrderItem) domain modellerini,
doğrulama kurallarını ve durum enum değerlerini içerir.
==============================================================================
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict

# Standart e-posta formatı doğrulama deseni (Regex)
EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
CustomerEmail = Annotated[
    str,
    Field(
        pattern=EMAIL_PATTERN,
        description="Geçerli bir e-posta adresi (Örn: eren@example.com)",
        examples=["eren.albayrak@example.com"],
    )
]


class OrderStatus(str, Enum):
    """Sipariş durumlarını temsil eden Enum sınıfı."""
    PENDING = "PENDING"          # Beklemede
    CONFIRMED = "CONFIRMED"      # Onaylandı
    CANCELLED = "CANCELLED"      # İptal Edildi
    COMPLETED = "COMPLETED"      # Tamamlandı


class OrderItemCreate(BaseModel):
    """
    Sipariş oluşturulurken gönderilen tek bir ürün kalemi şeması.
    """
    product_id: int = Field(
        ...,
        gt=0,
        description="Sipariş edilecek ürünün ID numarası",
        examples=[1],
    )
    quantity: int = Field(
        ...,
        gt=0,
        description="Sipariş edilecek ürün adedi (en az 1 olmalıdır)",
        examples=[2],
    )


class OrderItemResponse(BaseModel):
    """
    API yanıtında dönen sipariş kalemi detay şeması.
    Birim fiyat (unit_price) sipariş anındaki ürün fiyatı üzerinden sunucu tarafından atanır.
    """
    id: int = Field(..., description="Sipariş kalemi benzersiz ID'si", examples=[1])
    product_id: int = Field(..., description="Ürün ID'si", examples=[1])
    quantity: int = Field(..., description="Sipariş edilen adet", examples=[2])
    unit_price: float = Field(
        ...,
        description="Sipariş anındaki ürün birim fiyatı",
        examples=[1899.90],
    )

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    """
    Yeni sipariş oluşturma (POST /orders/) isteğinde beklenen veri şeması.
    """
    customer_email: CustomerEmail
    items: List[OrderItemCreate] = Field(
        ...,
        min_length=1,
        description="Siparişte yer alan ürün kalemleri listesi (en az 1 kalem içermelidir)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer_email": "eren.albayrak@example.com",
                "items": [
                    {
                        "product_id": 1,
                        "quantity": 2
                    },
                    {
                        "product_id": 3,
                        "quantity": 1
                    }
                ]
            }
        }
    )


class OrderStatusUpdate(BaseModel):
    """
    Siparişin durumunu güncellemek (PATCH /orders/{id}/status) için kullanılan şema.
    """
    status: OrderStatus = Field(
        ...,
        description="Yeni sipariş durumu (PENDING, CONFIRMED, CANCELLED, COMPLETED)",
        examples=[OrderStatus.CONFIRMED],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "CONFIRMED"
            }
        }
    )


class OrderResponse(BaseModel):
    """
    API tarafından istemciye dönülen tam sipariş nesnesi.
    """
    id: int = Field(..., description="Siparişin benzersiz ID'si", examples=[1])
    customer_email: CustomerEmail
    total_amount: float = Field(..., description="Toplam sipariş tutarı (TL)", examples=[7999.80])
    status: OrderStatus = Field(..., description="Güncel sipariş durumu", examples=[OrderStatus.PENDING])
    items: List[OrderItemResponse] = Field(..., description="Sipariş kalemleri listesi")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Siparişin oluşturulma zamanı (UTC)",
        examples=["2026-08-31T10:00:00Z"],
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "customer_email": "eren.albayrak@example.com",
                "total_amount": 7999.80,
                "status": "PENDING",
                "items": [
                    {
                        "id": 1,
                        "product_id": 1,
                        "quantity": 2,
                        "unit_price": 1899.90
                    },
                    {
                        "id": 2,
                        "product_id": 3,
                        "quantity": 1,
                        "unit_price": 4200.00
                    }
                ],
                "created_at": "2026-08-31T10:00:00Z"
            }
        },
    )
