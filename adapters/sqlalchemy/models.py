"""
==============================================================================
SQLAlchemy ORM Tablo Modelleri (Data Models & Mappings)
==============================================================================
Cosmic Python standartlarında, veritabanı tabloları ve ilişkilerini
tanımlayan deklaratif ORM modelleri.
==============================================================================
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ==============================================================================
# Ürün - Kategori Çoka-Çok İlişki Tablosu (Many-to-Many Association Table)
# ==============================================================================
product_categories = Table(
    "product_categories",
    Base.metadata,
    Column(
        "product_id",
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "category_id",
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ==============================================================================
# 1. Kategori Tablo Modeli (Category Entity)
# ==============================================================================
class CategoryModel(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Çift yönlü ilişki
    products = relationship(
        "ProductModel",
        secondary=product_categories,
        back_populates="categories",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Kategori modelini şema uyumlu sözlüğe dönüştürür."""
        dt = self.created_at
        if isinstance(dt, datetime):
            dt = dt.isoformat()
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": dt,
        }


# ==============================================================================
# 2. Ürün Tablo Modeli (Product Entity)
# ==============================================================================
class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Çift yönlü ilişki
    categories = relationship(
        "CategoryModel",
        secondary=product_categories,
        back_populates="products",
        lazy="joined",
        order_by="CategoryModel.id.asc()",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Ürün modelini şema uyumlu sözlüğe dönüştürür."""
        dt = self.created_at
        if isinstance(dt, datetime):
            dt = dt.isoformat()
        cat_dicts = sorted(
            [c.to_dict() for c in (self.categories or [])],
            key=lambda x: x["id"],
        )
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "stock": int(self.stock),
            "is_active": bool(self.is_active),
            "created_at": dt,
            "category_ids": [c["id"] for c in cat_dicts],
            "categories": cat_dicts,
        }


# ==============================================================================
# 3. Sipariş Kalemi Tablo Modeli (OrderItem Entity)
# ==============================================================================
class OrderItemModel(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
    )
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    order = relationship("OrderModel", back_populates="items")

    def to_dict(self) -> Dict[str, Any]:
        """Sipariş kalemi modelini şema uyumlu sözlüğe dönüştürür."""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "quantity": int(self.quantity),
            "unit_price": float(self.unit_price),
        }


# ==============================================================================
# 4. Sipariş Tablo Modeli (Order Entity)
# ==============================================================================
class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_email = Column(String(255), nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    items = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="joined",
        order_by="OrderItemModel.id.asc()",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Sipariş modelini şema uyumlu sözlüğe dönüştürür."""
        dt = self.created_at
        if isinstance(dt, datetime):
            dt = dt.isoformat()
        return {
            "id": self.id,
            "customer_email": self.customer_email,
            "total_amount": float(self.total_amount),
            "status": self.status,
            "created_at": dt,
            "items": [item.to_dict() for item in (self.items or [])],
        }
