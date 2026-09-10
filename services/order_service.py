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
from services.cache_service import CacheService, cache_service
from events.base import EventPublisher, event_bus
from events.domain_events import (
    OrderCreatedEvent,
    OrderStatusChangedEvent,
)


class OrderService:
    """
    Sipariş işlemlerini yöneten, Redis Cache-Aside ve Observer Pattern destekli iş mantığı sınıfı.
    """

    def __init__(
        self,
        repository: Optional[IOrderRepository] = None,
        cache: Optional[CacheService] = None,
        bus: Optional[EventPublisher] = None,
    ) -> None:
        """
        Servisi soyut bağımlılıklar ile başlatır (Dependency Injection).
        """
        self.db: IOrderRepository = repository if repository is not None else get_database()
        self.cache: CacheService = cache if cache is not None else cache_service
        self.bus: EventPublisher = bus if bus is not None else event_bus

    def create_order(self, order_in: OrderCreate) -> OrderResponse:
        """
        Yeni bir sipariş oluşturur.
        1. Ürünlerin varlığını ve aktiflik durumunu doğrular.
        2. Stok kontrolü yapar (yetersiz stokta ValueError fırlatır).
        3. Güvenlik için birim fiyatları doğrudan veritabanından alıp toplam tutarı hesaplar.
        4. Sipariş ve kalemlerini atomik olarak kaydeder, ürün stoklarını eksiltir.
        5. OrderCreatedEvent yayınlar (Stok uyarıları, cache temizleme ve e-posta bildirimi tetiklenir).
        """
        items_data = [item.model_dump() for item in order_in.items]
        created_order_dict = self.db.create_order_atomic(
            customer_email=order_in.customer_email,
            items_data=items_data
        )
        response = OrderResponse.model_validate(created_order_dict)

        # Observer Pattern: Olayı yayınla
        self.bus.publish(
            OrderCreatedEvent(
                order_id=response.id,
                customer_email=response.customer_email,
                total_amount=response.total_amount,
                items=[item.model_dump() for item in response.items],
                payload=response.model_dump(),
            )
        )

        return response

    def get_order_by_id(self, order_id: int) -> Optional[OrderResponse]:
        """
        ID'ye göre siparişi Cache-Aside stratejisiyle kalemleriyle birlikte getirir.
        """
        cache_key = f"orders:item:{order_id}"

        def fetch_from_db():
            order_dict = self.db.get_order_by_id(order_id)
            if not order_dict:
                return None
            return order_dict

        cached_dict = self.cache.get_or_set(cache_key, fetch_from_db, ttl_seconds=60)
        if not cached_dict:
            return None
        return OrderResponse.model_validate(cached_dict)

    def list_orders(
        self,
        customer_email: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> List[OrderResponse]:
        """
        Siparişleri müşteri e-postası, sipariş durumu ve sayfalama parametrelerine göre Cache-Aside ile listeler.
        """
        status_val = status.value if status else None
        cache_key = f"orders:list:email={customer_email}:status={status_val}:skip={skip}:limit={limit}"

        def fetch_from_db():
            orders_list = self.db.get_all_orders(customer_email=customer_email, status=status_val)
            return orders_list[skip : skip + limit]

        cached_records = self.cache.get_or_set(cache_key, fetch_from_db, ttl_seconds=30)
        return [OrderResponse.model_validate(item) for item in cached_records]

    def update_order_status(self, order_id: int, status_in: OrderStatusUpdate) -> Optional[OrderResponse]:
        """
        Sipariş durumunu günceller (PENDING, CONFIRMED, CANCELLED, COMPLETED) ve OrderStatusChangedEvent yayınlar.
        Eğer sipariş CANCELLED yapılırsa stoklar iade edilir.
        """
        old_order = self.db.get_order_by_id(order_id)
        old_status = old_order["status"] if old_order else "UNKNOWN"

        updated_dict = self.db.update_order_status_atomic(order_id, status_in.status.value)
        if not updated_dict:
            return None

        response = OrderResponse.model_validate(updated_dict)

        # Observer Pattern: Olayı yayınla
        self.bus.publish(
            OrderStatusChangedEvent(
                order_id=order_id,
                old_status=old_status,
                new_status=response.status.value,
                payload=response.model_dump(),
            )
        )

        return response


def get_order_service(
    repository: IOrderRepository = Depends(get_database)
) -> OrderService:
    """
    FastAPI Dependency Injection sağlayıcısı.
    Servise somut sınıf yerine IOrderRepository soyut arayüzünü enjekte eder.
    """
    return OrderService(repository=repository)

