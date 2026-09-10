"""
==============================================================================
Domain Olayları (Domain Events)
==============================================================================
Sistem içerisinde ürün, kategori ve sipariş süreçlerinde meydana gelen
tüm somut olay sınıflarını içerir.
==============================================================================
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from events.base import Event


# ==============================================================================
# 1. ÜRÜN DOMAIN OLAYLARI (PRODUCT EVENTS)
# ==============================================================================
@dataclass
class ProductCreatedEvent(Event):
    """Yeni bir ürün oluşturulduğunda fırlatılır."""
    product_id: int = 0
    name: str = ""
    price: float = 0.0
    stock: int = 0
    category_ids: List[int] = field(default_factory=list)


@dataclass
class ProductUpdatedEvent(Event):
    """Bir ürün güncellendiğinde veya aktifliği değiştirildiğinde fırlatılır."""
    product_id: int = 0
    updated_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductDeletedEvent(Event):
    """Bir ürün silindiğinde fırlatılır."""
    product_id: int = 0
    name: Optional[str] = None


# ==============================================================================
# 2. KATEGORİ DOMAIN OLAYLARI (CATEGORY EVENTS)
# ==============================================================================
@dataclass
class CategoryCreatedEvent(Event):
    """Yeni bir kategori eklendiğinde fırlatılır."""
    category_id: int = 0
    name: str = ""


@dataclass
class CategoryUpdatedEvent(Event):
    """Kategori bilgileri güncellendiğinde fırlatılır."""
    category_id: int = 0
    name: str = ""


@dataclass
class CategoryDeletedEvent(Event):
    """Bir kategori silindiğinde fırlatılır."""
    category_id: int = 0


# ==============================================================================
# 3. SİPARİŞ DOMAIN OLAYLARI (ORDER EVENTS)
# ==============================================================================
@dataclass
class OrderCreatedEvent(Event):
    """Yeni bir sipariş oluşturulduğunda ve stoklar atomik düşüldüğünde fırlatılır."""
    order_id: int = 0
    customer_email: str = ""
    total_amount: float = 0.0
    items: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class OrderStatusChangedEvent(Event):
    """Sipariş durumu güncellendiğinde (örn: PENDING -> COMPLETED / CANCELLED) fırlatılır."""
    order_id: int = 0
    old_status: str = ""
    new_status: str = ""
