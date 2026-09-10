"""
==============================================================================
Domain Events & Observer Pattern Package
==============================================================================
"""

from events.base import Event, Observer, EventPublisher, event_bus
from events.domain_events import (
    ProductCreatedEvent,
    ProductUpdatedEvent,
    ProductDeletedEvent,
    CategoryCreatedEvent,
    CategoryUpdatedEvent,
    CategoryDeletedEvent,
    OrderCreatedEvent,
    OrderStatusChangedEvent,
)
from events.observers import (
    CacheInvalidationObserver,
    StockAlertObserver,
    NotificationObserver,
    AuditLogObserver,
)

__all__ = [
    "Event",
    "Observer",
    "EventPublisher",
    "event_bus",
    "ProductCreatedEvent",
    "ProductUpdatedEvent",
    "ProductDeletedEvent",
    "CategoryCreatedEvent",
    "CategoryUpdatedEvent",
    "CategoryDeletedEvent",
    "OrderCreatedEvent",
    "OrderStatusChangedEvent",
    "CacheInvalidationObserver",
    "StockAlertObserver",
    "NotificationObserver",
    "AuditLogObserver",
]
