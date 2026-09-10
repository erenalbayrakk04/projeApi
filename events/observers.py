"""
==============================================================================
Somut Gözlemciler (Concrete Observers)
==============================================================================
Domain olaylarına tepki veren, iş mantığını servis katmanından ayıran
uzmanlaşmış gözlemci (Observer) sınıfları.
==============================================================================
"""

import logging
from typing import Any, Dict, List, Optional
from events.base import Event, Observer
from events.domain_events import (
    CategoryCreatedEvent,
    CategoryDeletedEvent,
    CategoryUpdatedEvent,
    OrderCreatedEvent,
    OrderStatusChangedEvent,
    ProductCreatedEvent,
    ProductDeletedEvent,
    ProductUpdatedEvent,
)

logger = logging.getLogger("observers")


# ==============================================================================
# 1. ÖNBELLEK GEÇERSİZ KILMA GÖZLEMCİSİ (CACHE INVALIDATION OBSERVER)
# ==============================================================================
class CacheInvalidationObserver(Observer):
    """
    Veritabanında ürün, kategori veya sipariş verisi değiştiğinde
    Redis önbelleğini otomatik olarak temizleyen gözlemci.
    """

    def __init__(self, cache_service: Optional[Any] = None) -> None:
        self._cache_service = cache_service

    @property
    def cache_service(self) -> Any:
        if self._cache_service is not None:
            return self._cache_service
        from services.cache_service import cache_service
        return cache_service

    def handle(self, event: Event) -> None:
        if isinstance(event, (ProductCreatedEvent, ProductUpdatedEvent, ProductDeletedEvent)):
            logger.info(f"🔄 [CacheInvalidation] {event.event_name} alındı -> Ürün önbelleği temizleniyor...")
            self.cache_service.invalidate_products()

        elif isinstance(event, (CategoryCreatedEvent, CategoryUpdatedEvent, CategoryDeletedEvent)):
            logger.info(f"🔄 [CacheInvalidation] {event.event_name} alındı -> Kategori ve ürün önbelleği temizleniyor...")
            self.cache_service.invalidate_categories()
            self.cache_service.invalidate_products()

        elif isinstance(event, (OrderCreatedEvent, OrderStatusChangedEvent)):
            logger.info(f"🔄 [CacheInvalidation] {event.event_name} alındı -> Sipariş ve ürün stok önbelleği temizleniyor...")
            self.cache_service.invalidate_orders()
            self.cache_service.invalidate_products()


# ==============================================================================
# 2. KRİTİK STOK UYARI GÖZLEMCİSİ (STOCK ALERT OBSERVER)
# ==============================================================================
class StockAlertObserver(Observer):
    """
    Sipariş verildiğinde veya stok güncellendiğinde, stok adedi kritik seviyenin
    (10 veya daha az) altına düşen ürünleri tespit edip uyarı üreten gözlemci.
    """

    def __init__(self, stock_threshold: int = 10, database: Optional[Any] = None) -> None:
        self.stock_threshold = stock_threshold
        self._db = database
        self.recent_alerts: List[Dict[str, Any]] = []

    @property
    def db(self) -> Any:
        if self._db is not None:
            return self._db
        from database import get_database
        return get_database()

    def handle(self, event: Event) -> None:
        if isinstance(event, OrderCreatedEvent):
            # Sipariş kalemlerindeki ürünlerin güncel stok durumlarını kontrol et
            for item in event.items:
                product_id = item.get("product_id")
                if not product_id:
                    continue

                prod = self.db.get_by_id(product_id)
                if prod:
                    stock = prod.get("stock", 0)
                    prod_name = prod.get("name", f"Ürün #{product_id}")

                    if stock == 0:
                        alert = {
                            "type": "OUT_OF_STOCK",
                            "product_id": product_id,
                            "product_name": prod_name,
                            "remaining_stock": 0,
                            "order_id": event.order_id,
                        }
                        self.recent_alerts.append(alert)
                        logger.warning(
                            f"🚨 [KRİTİK STOK UYARISI] '{prod_name}' (ID: #{product_id}) TÜKENDİ! (Kalan: 0)"
                        )
                    elif stock <= self.stock_threshold:
                        alert = {
                            "type": "LOW_STOCK",
                            "product_id": product_id,
                            "product_name": prod_name,
                            "remaining_stock": stock,
                            "order_id": event.order_id,
                        }
                        self.recent_alerts.append(alert)
                        logger.warning(
                            f"⚠️ [KRİTİK STOK UYARISI] '{prod_name}' (ID: #{product_id}) kritik seviyede! (Kalan Stok: {stock})"
                        )


# ==============================================================================
# 3. MÜŞTERİ BİLDİRİM GÖZLEMCİSİ (NOTIFICATION OBSERVER)
# ==============================================================================
class NotificationObserver(Observer):
    """
    Sipariş oluşturulduğunda veya durumu güncellendiğinde müşteri bildirim
    ve e-posta simülasyonunu yöneten gözlemci.
    """

    def __init__(self) -> None:
        self.sent_notifications: List[Dict[str, Any]] = []

    def handle(self, event: Event) -> None:
        if isinstance(event, OrderCreatedEvent):
            notification = {
                "recipient": event.customer_email,
                "type": "ORDER_CONFIRMATION",
                "subject": f"Siparişiniz Alındı! #{event.order_id}",
                "message": (
                    f"Sayın Müşterimiz, #{event.order_id} numaralı siparişiniz başarıyla oluşturuldu. "
                    f"Toplam Tutar: {event.total_amount:,.2f} ₺."
                ),
                "order_id": event.order_id,
            }
            self.sent_notifications.append(notification)
            logger.info(
                f"📧 [E-Posta Bildirimi] '{event.customer_email}' adresine Sipariş #{event.order_id} onay mesajı gönderildi."
            )

        elif isinstance(event, OrderStatusChangedEvent):
            notification = {
                "type": "ORDER_STATUS_UPDATED",
                "order_id": event.order_id,
                "old_status": event.old_status,
                "new_status": event.new_status,
                "message": f"Sipariş #{event.order_id} durumu '{event.old_status}' -> '{event.new_status}' olarak güncellendi.",
            }
            self.sent_notifications.append(notification)
            logger.info(
                f"🔔 [Durum Bildirimi] Sipariş #{event.order_id} yeni durumu: {event.new_status}."
            )


# ==============================================================================
# 4. GÜVENLİK VE DENETİM GÜNLÜĞÜ GÖZLEMCİSİ (AUDIT LOG OBSERVER)
# ==============================================================================
class AuditLogObserver(Observer):
    """
    Sistemde tetiklenen tüm olayları (Domain Events) denetim kaydı (Audit Log)
    olarak hafızada ve log dosyalarında saklayan genel gözlemci.
    """

    def __init__(self) -> None:
        self.audit_logs: List[Dict[str, Any]] = []

    def handle(self, event: Event) -> None:
        log_entry = {
            "event_id": event.event_id,
            "event_name": event.event_name,
            "timestamp": event.timestamp.isoformat(),
            "payload": event.payload,
        }
        self.audit_logs.append(log_entry)
        logger.debug(f"📝 [AuditLog] Olay Kaydedildi: {event.event_name} (ID: {event.event_id[:8]})")
