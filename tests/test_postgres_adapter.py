"""
==============================================================================
Cosmic Python Repository Pattern & Adaptör Testleri
==============================================================================
Bu test paketi:
1. SqlAlchemyDatabase adaptörünün IDatabase sözleşmesine %100 uyumluluğunu,
2. Cosmic Python FakeRepository (In-Memory) deposunun sözleşme ve CRUD uyumluluğunu,
3. Veritabanı Fabrikası (DB Factory) ve DatabaseProxy mekanizmasını
doğrular.
==============================================================================
"""

import os
import pytest

from interfaces.repositories import (
    IDatabase,
    IProductRepository,
    ICategoryRepository,
    IOrderRepository,
)
from adapters.sqlalchemy.database import SqlAlchemyDatabase
from adapters.fake.fake_repository import FakeRepository
from database import get_database, _DatabaseProxy


# ==============================================================================
# 1. Arayüz ve Sözleşme Uyumluluk Testleri (Interface Compliance)
# ==============================================================================
def test_sqlalchemy_database_implements_interfaces():
    """
    SqlAlchemyDatabase sınıfının IDatabase ve alt Repository arayüzlerini
    eksiksiz implemente ettiğini doğrular.
    """
    assert issubclass(SqlAlchemyDatabase, IDatabase)
    assert issubclass(SqlAlchemyDatabase, IProductRepository)
    assert issubclass(SqlAlchemyDatabase, ICategoryRepository)
    assert issubclass(SqlAlchemyDatabase, IOrderRepository)

    db_instance = SqlAlchemyDatabase("sqlite:///:memory:")
    assert isinstance(db_instance, IDatabase)
    assert isinstance(db_instance, IProductRepository)
    assert isinstance(db_instance, ICategoryRepository)
    assert isinstance(db_instance, IOrderRepository)


def test_fake_repository_implements_interfaces():
    """
    Cosmic Python FakeRepository sınıfının IDatabase arayüzünü
    eksiksiz uyguladığını doğrular.
    """
    assert issubclass(FakeRepository, IDatabase)
    assert issubclass(FakeRepository, IProductRepository)
    assert issubclass(FakeRepository, ICategoryRepository)
    assert issubclass(FakeRepository, IOrderRepository)

    fake_db = FakeRepository()
    assert isinstance(fake_db, IDatabase)


# ==============================================================================
# 2. Veritabanı Fabrikası (DB Factory) Testleri
# ==============================================================================
def test_db_factory_returns_database_instance(monkeypatch):
    """
    get_database() çağrısının IDatabase uygulayan bir adaptör döndüğünü doğrular.
    """
    import database
    database._active_database_instance = None

    db = get_database()
    assert isinstance(db, IDatabase)
    assert hasattr(db, "get_all")
    assert hasattr(db, "add_category")
    assert hasattr(db, "create_order_atomic")


def test_database_proxy_delegation():
    """
    Global db (DatabaseProxy) nesnesinin çağrıları aktif adaptöre ilettiğini doğrular.
    """
    import database
    proxy = database.db
    assert repr(proxy).startswith("<DatabaseProxy")
    assert hasattr(proxy, "clear")
    assert hasattr(proxy, "get_all")
    assert hasattr(proxy, "add_category")
    assert hasattr(proxy, "create_order_atomic")


# ==============================================================================
# 3. Cosmic Python Fake Repository CRUD ve Atomik Sipariş Testleri
# ==============================================================================
def test_fake_repository_crud_flow():
    """
    FakeRepository üzerinde Kategori, Ürün ve Sipariş işlemlerinin
    in-memory olarak hatasız çalıştığını test eder.
    """
    fake = FakeRepository()
    fake.clear()

    # 1. Kategori Ekle
    cat = fake.add_category({"name": "Test Kategori", "description": "Açıklama"})
    assert cat["id"] == 1
    assert cat["name"] == "Test Kategori"

    # 2. Ürün Ekle
    prod = fake.add({
        "name": "Test Klavye",
        "description": "RGB",
        "price": 500.0,
        "stock": 10,
        "category_ids": [1],
        "is_active": True,
    })
    assert prod["id"] == 1
    assert prod["stock"] == 10

    # 3. Sipariş Oluştur
    order = fake.create_order_atomic(
        customer_email="test@example.com",
        items_data=[{"product_id": 1, "quantity": 3}],
    )
    assert order["id"] == 1
    assert order["total_amount"] == 1500.0

    # Stok kontrolü (10 - 3 = 7 kalmalı)
    updated_prod = fake.get_by_id(1)
    assert updated_prod is not None
    assert updated_prod["stock"] == 7

    # 4. Sipariş İptali ve Stok İadesi
    cancelled_order = fake.update_order_status_atomic(order["id"], "CANCELLED")
    assert cancelled_order is not None
    assert cancelled_order["status"] == "CANCELLED"

    restored_prod = fake.get_by_id(1)
    assert restored_prod is not None
    assert restored_prod["stock"] == 10
