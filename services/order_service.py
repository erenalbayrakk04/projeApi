"""
==============================================================================
Sipariş Servis Katmanı (Order Service - İş Mantığı Katmanı)
==============================================================================
Bu modül, sipariş oluşturma, stok doğrulama ve düşümü, fiyat hesaplaması,
durum güncellemeleri ve sipariş listeleme iş mantıklarını yürütür.

SOLID Prensipleri:
- Dependency Inversion Principle (DIP): OrderService somut SQLiteDatabase sınıfına
  değil, soyut IOrderRepository arayüzüne bağımlıdır.
==============================================================================
"""

from typing import List, Optional
from fastapi import Depends
from interfaces.repositories import IOrderRepository
from database import get_database
from schemas.order import (
    OrderCreate,
    OrderStatusUpdate,
    OrderResponse,
    OrderStatus,
)


class OrderService:
    """
    Sipariş işlemlerini yöneten iş mantığı sınıfı.
    """

    def __init__(self, repository: Optional[IOrderRepository] = None) -> None:
        """
        Servisi soyut IOrderRepository arayüzü ile başlatır (Dependency Injection).
        """
        self.db: IOrderRepository = repository if repository is not None else get_database()

    def create_order(self, order_in: OrderCreate) -> OrderResponse:
        """
        Yeni bir sipariş oluşturur.
        1. Ürünlerin varlığını ve aktiflik durumunu doğrular.
        2. Stok kontrolü yapar (yetersiz stokta ValueError fırlatır).
        3. Güvenlik için birim fiyatları doğrudan veritabanından alıp toplam tutarı hesaplar.
        4. Sipariş ve kalemlerini atomik olarak kaydeder, ürün stoklarını eksiltir.
        """
        items_data = [item.model_dump() for item in order_in.items]
        created_order_dict = self.db.create_order_atomic(
            customer_email=order_in.customer_email,
            items_data=items_data
        )
        return OrderResponse.model_validate(created_order_dict)

    def get_order_by_id(self, order_id: int) -> Optional[OrderResponse]:
        """
        ID'ye göre siparişi kalemleriyle birlikte getirir.
        """
        order_dict = self.db.get_order_by_id(order_id)
        if not order_dict:
            return None
        return OrderResponse.model_validate(order_dict)

    def list_orders(
        self,
        customer_email: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> List[OrderResponse]:
        """
        Siparişleri müşteri e-postası, sipariş durumu ve sayfalama parametrelerine göre listeler.
        """
        status_val = status.value if status else None
        orders_list = self.db.get_all_orders(customer_email=customer_email, status=status_val)
        paginated = orders_list[skip : skip + limit]
        return [OrderResponse.model_validate(item) for item in paginated]

    def update_order_status(self, order_id: int, status_in: OrderStatusUpdate) -> Optional[OrderResponse]:
        """
        Sipariş durumunu günceller (PENDING, CONFIRMED, CANCELLED, COMPLETED).
        Eğer sipariş CANCELLED yapılırsa stoklar iade edilir.
        """
        updated_dict = self.db.update_order_status_atomic(order_id, status_in.status.value)
        if not updated_dict:
            return None
        return OrderResponse.model_validate(updated_dict)


def get_order_service(
    repository: IOrderRepository = Depends(get_database)
) -> OrderService:
    """
    FastAPI Dependency Injection sağlayıcısı.
    Servise somut sınıf yerine IOrderRepository soyut arayüzünü enjekte eder.
    """
    return OrderService(repository=repository)
