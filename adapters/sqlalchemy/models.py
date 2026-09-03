"""
==============================================================================
SQLAlchemy ORM Tablo Modelleri (Data Models & Mappings)
==============================================================================
Cosmic Python ve SQLAlchemy 2.0 standartlarında, tip güvenliği tam (Mapped)
tablo ve ilişki modelleri.
==============================================================================
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 Deklaratif Temel Sınıfı."""
    pass


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

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Çift yönlü ilişki
    products: Mapped[List["ProductModel"]] = relationship(
        "ProductModel",
        secondary=product_categories,
        back_populates="categories",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Kategori modelini şema uyumlu sözlüğe dönüştürür."""
        dt = self.created_at
        formatted_dt = dt.isoformat() if isinstance(dt, datetime) else str(dt)
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": formatted_dt,
        }


# ==============================================================================
# 2. Ürün Tablo Modeli (Product Entity)
# ==============================================================================
class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Çift yönlü ilişki
    categories: Mapped[List["CategoryModel"]] = relationship(
        "CategoryModel",
        secondary=product_categories,
        back_populates="products",
        lazy="joined",
        order_by="CategoryModel.id.asc()",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Ürün modelini şema uyumlu sözlüğe dönüştürür."""
        dt = self.created_at
        formatted_dt = dt.isoformat() if isinstance(dt, datetime) else str(dt)
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
            "created_at": formatted_dt,
            "category_ids": [c["id"] for c in cat_dicts],
            "categories": cat_dicts,
        }


# ==============================================================================
# 3. Sipariş Kalemi Tablo Modeli (OrderItem Entity)
# ==============================================================================
class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["OrderModel"] = relationship("OrderModel", back_populates="items")

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

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    items: Mapped[List["OrderItemModel"]] = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="joined",
        order_by="OrderItemModel.id.asc()",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Sipariş modelini şema uyumlu sözlüğe dönüştürür."""
        dt = self.created_at
        formatted_dt = dt.isoformat() if isinstance(dt, datetime) else str(dt)
        return {
            "id": self.id,
            "customer_email": self.customer_email,
            "total_amount": float(self.total_amount),
            "status": self.status,
            "created_at": formatted_dt,
            "items": [item.to_dict() for item in (self.items or [])],
        }
