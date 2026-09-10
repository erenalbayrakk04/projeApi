"""
==============================================================================
Observer Pattern & Event-Driven Architecture Unit & Integration Tests
==============================================================================
Bu modül, EventPublisher (Event Bus), Domain Events ve Concrete Observers
bileşenlerinin doğru çalıştığını, olayların izole şekilde dağıtıldığını ve
hata izolasyonunun sağlandığını test eder.
==============================================================================
"""

import pytest
from events.base import Event, Observer, EventPublisher, event_bus
from events.domain_events import (
    ProductCreatedEvent,
    ProductUpdatedEvent,
    ProductDeletedEvent,
    CategoryCreatedEvent,
    OrderCreatedEvent,
    OrderStatusChangedEvent,
)
from events.observers import (
    CacheInvalidationObserver,
    StockAlertObserver,
    NotificationObserver,
    AuditLogObserver,
)
from services.product_service import ProductService
from services.order_service import OrderService
from schemas.product import ProductCreate, ProductUpdate
from schemas.order import OrderCreate, OrderItemCreate, OrderStatusUpdate, OrderStatus


class MockCustomObserver(Observer):
    def __init__(self):
        self.received_events = []

    def handle(self, event: Event) -> None:
        self.received_events.append(event)


class FailingObserver(Observer):
    def handle(self, event: Event) -> None:
        raise RuntimeError("Simulated observer internal failure")


def test_event_publisher_subscribe_and_publish():
    bus = EventPublisher()
    mock_obs = MockCustomObserver()

    bus.subscribe(ProductCreatedEvent, mock_obs)
    event = ProductCreatedEvent(product_id=1, name="Laptop", price=15000.0, stock=5)
    bus.publish(event)

    assert len(mock_obs.received_events) == 1
    assert mock_obs.received_events[0].product_id == 1
    assert mock_obs.received_events[0].name == "Laptop"


def test_event_publisher_selective_vs_global_subscription():
    bus = EventPublisher()
    product_obs = MockCustomObserver()
    global_obs = MockCustomObserver()

    bus.subscribe(ProductCreatedEvent, product_obs)
    bus.subscribe_all(global_obs)

    # 1. ProductCreatedEvent yayınla -> İkisi de almalı
    bus.publish(ProductCreatedEvent(product_id=10, name="Mouse"))
    assert len(product_obs.received_events) == 1
    assert len(global_obs.received_events) == 1

    # 2. CategoryCreatedEvent yayınla -> Sadece global_obs almalı
    bus.publish(CategoryCreatedEvent(category_id=2, name="Aksesuar"))
    assert len(product_obs.received_events) == 1
    assert len(global_obs.received_events) == 2


def test_event_publisher_unsubscription():
    bus = EventPublisher()
    obs = MockCustomObserver()

    bus.subscribe(ProductCreatedEvent, obs)
    bus.publish(ProductCreatedEvent(product_id=1))
    assert len(obs.received_events) == 1

    bus.unsubscribe(ProductCreatedEvent, obs)
    bus.publish(ProductCreatedEvent(product_id=2))
    assert len(obs.received_events) == 1


def test_event_publisher_fault_tolerance():
    bus = EventPublisher()
    failing_obs = FailingObserver()
    working_obs = MockCustomObserver()

    bus.subscribe(failing_obs)
    bus.subscribe(working_obs)

    # Hata fırlatılmamalı, yakalanıp loglanmalı
    bus.publish(ProductCreatedEvent(product_id=99, name="Robust Item"))

    assert len(working_obs.received_events) == 1
    assert working_obs.received_events[0].product_id == 99


def test_stock_alert_observer_triggers_on_low_stock():
    """Stok kritik seviyenin (<= 10) altına indiğinde StockAlertObserver'ın uyarı ürettiğini test eder."""
    stock_obs = StockAlertObserver(stock_threshold=10)
    event_bus.subscribe(stock_obs)

    order_service = OrderService()
    # Mevcut test seed verisinde Ürün #1 stok: 35
    # 30 adet sipariş verilince kalan stok: 5 (<= 10, LOW_STOCK tetiklenmeli)
    order_in = OrderCreate(
        customer_email="buyer@example.com",
        items=[OrderItemCreate(product_id=1, quantity=30)]
    )
    order_service.create_order(order_in)

    assert len(stock_obs.recent_alerts) > 0
    alert = stock_obs.recent_alerts[-1]
    assert alert["type"] == "LOW_STOCK"
    assert alert["product_id"] == 1
    assert alert["remaining_stock"] == 5


def test_notification_observer_on_order_lifecycle():
    notif_obs = NotificationObserver()
    event_bus.subscribe(notif_obs)

    order_service = OrderService()
    order_in = OrderCreate(
        customer_email="customer@example.com",
        items=[OrderItemCreate(product_id=1, quantity=1)]
    )
    created = order_service.create_order(order_in)

    # 1. Sipariş onay bildirimi
    assert len(notif_obs.sent_notifications) == 1
    assert notif_obs.sent_notifications[0]["type"] == "ORDER_CONFIRMATION"
    assert notif_obs.sent_notifications[0]["recipient"] == "customer@example.com"

    # 2. Durum güncelleme bildirimi
    order_service.update_order_status(created.id, OrderStatusUpdate(status=OrderStatus.COMPLETED))
    assert len(notif_obs.sent_notifications) == 2
    assert notif_obs.sent_notifications[1]["type"] == "ORDER_STATUS_UPDATED"
    assert notif_obs.sent_notifications[1]["new_status"] == "COMPLETED"


def test_audit_log_observer_records_all_events():
    audit_obs = AuditLogObserver()
    event_bus.subscribe(audit_obs)

    prod_service = ProductService()
    prod = prod_service.create_product(
        ProductCreate(name="Denetim Ürünü", price=250.0, stock=20, category_ids=[1])
    )
    prod_service.update_product(
        prod.id, ProductUpdate(name="Denetim Ürünü Güncel", price=300.0, stock=18, category_ids=[1], is_active=True)
    )
    prod_service.delete_product(prod.id)

    event_names = [log["event_name"] for log in audit_obs.audit_logs]
    assert "ProductCreatedEvent" in event_names
    assert "ProductUpdatedEvent" in event_names
    assert "ProductDeletedEvent" in event_names
