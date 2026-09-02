"""
==============================================================================
Sipariş Yönlendirici Katmanı (Order Router - HTTP Presentation Layer)
==============================================================================
Bu modül, /orders altındaki sipariş oluşturma, listeleme ve durum güncelleme
API endpoint'lerini tanımlar.
==============================================================================
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from schemas.order import (
    OrderCreate,
    OrderStatusUpdate,
    OrderResponse,
    OrderStatus,
)
from services.order_service import OrderService, get_order_service

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    responses={
        404: {"description": "Sipariş veya ürün bulunamadı (Not Found)."},
        400: {"description": "Geçersiz istek veya yetersiz stok (Bad Request)."},
        422: {"description": "Pydantic şema doğrulama hatası (Unprocessable Entity)."},
    },
)


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni sipariş oluştur",
    description="Sipariş kalemlerindeki ürünlerin stok durumunu kontrol eder, stokları düşer ve siparişi kaydeder.",
)
def create_order(
    order_in: OrderCreate,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    """
    Yeni sipariş oluşturma endpoint'i:
    - İstenen ürün sistemde yoksa **404 Not Found** döner.
    - Stok yetersiz veya ürün pasifse **400 Bad Request** döner.
    - Başarılı ise **201 Created** ile sipariş detayları ve hesaplanan toplam tutar döner.
    """
    try:
        return service.create_order(order_in)
    except ValueError as err:
        err_msg = str(err)
        if "bulunamadı" in err_msg.lower() or "not found" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=err_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg,
            )


@router.get(
    "/",
    response_model=List[OrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Siparişleri listele ve filtrele",
    description="Müşteri e-postası ve sipariş durumuna göre filtreleme ve sayfalama destekler.",
)
def list_orders(
    customer_email: Optional[str] = Query(
        default=None,
        description="Müşteri e-posta adresine göre filtrele",
        examples=["eren.albayrak@example.com"],
    ),
    status_filter: Optional[OrderStatus] = Query(
        default=None,
        alias="status",
        description="Sipariş durumuna göre filtrele (PENDING, CONFIRMED, CANCELLED, COMPLETED)",
    ),
    skip: int = Query(default=0, ge=0, description="Atlanacak kayıt sayısı"),
    limit: int = Query(default=10, ge=1, le=100, description="Maksimum getirilecek kayıt sayısı"),
    service: OrderService = Depends(get_order_service),
) -> List[OrderResponse]:
    """
    Sipariş listeleme endpoint'i.
    """
    return service.list_orders(
        customer_email=customer_email,
        status=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="ID ile tekil sipariş detayını getir",
    description="Belirtilen ID numaralı siparişin ve kalemlerinin tam detayını getirir.",
)
def get_order(
    order_id: int,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    """
    ID ile sipariş sorgulama endpoint'i:
    - Sipariş bulunamazsa **404 Not Found** döner.
    """
    order = service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID numarası '{order_id}' olan sipariş bulunamadı.",
        )
    return order


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Sipariş durumunu güncelle",
    description="Siparişin durumunu günceller. Eğer sipariş CANCELLED yapılırsa stoklar iade edilir.",
)
def update_order_status(
    order_id: int,
    status_in: OrderStatusUpdate,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    """
    Sipariş durumu güncelleme endpoint'i:
    - Sipariş bulunamazsa **404 Not Found** döner.
    - İptal edilen sipariş yeniden aktif edilirken stok yetersiz kalırsa **400 Bad Request** döner.
    """
    try:
        updated_order = service.update_order_status(order_id, status_in)
        if not updated_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID numarası '{order_id}' olan sipariş bulunamadı.",
            )
        return updated_order
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
