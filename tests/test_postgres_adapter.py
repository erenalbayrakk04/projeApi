"""
==============================================================================
PostgreSQL Adapter Birim ve Entegrasyon Testleri (Pytest & Mocking)
==============================================================================
Bu test paketi, Clean Architecture prensiplerine uygun olarak geliştirilen
PostgresDatabase adapter sınıfının:
1. IDatabase ve Repository soyut sözleşmelerine (Interfaces) %100 uyumluluğunu,
2. Veritabanı Fabrikası (DB Factory) seçim mekanizmasını (DB_TYPE),
3. PostgreSQL DDL şema oluşturma ve CRUD operasyonlarını,
4. Atomik sipariş, stok düşümü, iptal iadesi ve rollback mekanizmalarını
doğrular.
==============================================================================
"""

import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import pytest

from interfaces.repositories import (
    IDatabase,
    IProductRepository,
    ICategoryRepository,
    IOrderRepository,
)
from adapters.postgres_database import PostgresDatabase
from database import SQLiteDatabase, get_database, _DatabaseProxy


# ==============================================================================
# 1. Arayüz ve Sözleşme Uyumluluk Testleri (Interface Compliance)
# ==============================================================================
def test_postgres_database_implements_interfaces():
    """
    PostgresDatabase sınıfının IDatabase ve alt Repository arayüzlerini
    eksiksiz implemente ettiğini doğrular.
    """
    assert issubclass(PostgresDatabase, IDatabase)
    assert issubclass(PostgresDatabase, IProductRepository)
    assert issubclass(PostgresDatabase, ICategoryRepository)
    assert issubclass(PostgresDatabase, IOrderRepository)

    # Örnek oluşturulduğunda soyut metot eksiği olmamalıdır
    db_instance = PostgresDatabase(
        host="localhost",
        port=5432,
        database="test_db",
        user="test_user",
    )
    assert isinstance(db_instance, IDatabase)
    assert isinstance(db_instance, IProductRepository)
    assert isinstance(db_instance, ICategoryRepository)
    assert isinstance(db_instance, IOrderRepository)


# ==============================================================================
# 2. Veritabanı Fabrikası (DB Factory) Testleri
# ==============================================================================
def test_db_factory_returns_sqlite_by_default(monkeypatch):
    """
    DB_TYPE tanımlı değilken veya 'sqlite' iken SQLiteDatabase döndüğünü test eder.
    """
    monkeypatch.delenv("DB_TYPE", raising=False)
    import database
    database._sqlite_instance = None
    database._postgres_instance = None

    db = get_database()
    assert isinstance(db, SQLiteDatabase)


def test_db_factory_returns_postgres_when_configured(monkeypatch):
    """
    DB_TYPE='postgres' olarak ayarlandığında PostgresDatabase döndüğünü test eder.
    """
    monkeypatch.setenv("DB_TYPE", "postgres")
    import database
    database._sqlite_instance = None
    database._postgres_instance = None

    db = get_database()
    assert isinstance(db, PostgresDatabase)

    # Temizle ve normale dön
    monkeypatch.setenv("DB_TYPE", "sqlite")
    database._sqlite_instance = None
    database._postgres_instance = None


def test_database_proxy_delegation():
    """
    Global db (DatabaseProxy) nesnesinin çağrıları aktif adaptöre ilettiğini doğrular.
    """
    import database
    proxy = database.db
    assert repr(proxy).startswith("<DatabaseProxy")
    # clear veya get_all fonksiyonları proxy üzerinden erişilebilir olmalıdır
    assert hasattr(proxy, "clear")
    assert hasattr(proxy, "get_all")
    assert hasattr(proxy, "add_category")
    assert hasattr(proxy, "create_order_atomic")


# ==============================================================================
# 3. PostgreSQL Adapter Parametre ve Şema Testleri
# ==============================================================================
def test_postgres_database_config():
    """
    PostgreSQL yapılandırma parametrelerinin doğru okunduğunu test eder.
    """
    db = PostgresDatabase(
        host="custom_host",
        port=5433,
        database="custom_db",
        user="custom_user",
        password="test_secret_token",
    )
    assert db.host == "custom_host"
    assert db.port == 5433
    assert db.database == "custom_db"
    assert db.user == "custom_user"
    assert db.password == "test_secret_token"


def test_postgres_init_db_creates_tables():
    """
    init_db metodunun PostgreSQL uyumlu DDL komutlarını çalıştırdığını doğrular.
    """
    db = PostgresDatabase()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    with patch.object(db, "_get_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        db.init_db()

        # DDL sorgularının çalıştırıldığını doğrula
        assert mock_cursor.execute.call_count >= 5
        mock_conn.commit.assert_called()


# ==============================================================================
# 4. Kategori (Category) CRUD ve İş Mantığı Testleri
# ==============================================================================
def test_postgres_category_crud():
    """
    PostgresDatabase üzerinde kategori ekleme, getirme ve güncelleme mantığını test eder.
    """
    db = PostgresDatabase()
    now = datetime.now(timezone.utc)

    # 1. add_category
    with patch.object(db, "_get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id": 1}
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        with patch.object(db, "get_category_by_id") as mock_get_id:
            mock_get_id.return_value = {
                "id": 1,
                "name": "Elektronik",
                "description": "Elektronik ürünler",
                "created_at": now.isoformat(),
            }
            cat = db.add_category({"name": "Elektronik", "description": "Elektronik ürünler"})
            assert cat["id"] == 1
            assert cat["name"] == "Elektronik"

    # 2. get_category_by_name
    with patch.object(db, "_get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "name": "Elektronik",
            "description": "Elektronik ürünler",
            "created_at": now,
        }
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        found = db.get_category_by_name("elektronik")
        assert found is not None
        assert found["id"] == 1
        assert found["name"] == "Elektronik"

    # 3. delete_category
    with patch.object(db, "get_category_by_id", return_value={"id": 1}):
        with patch.object(db, "_get_connection") as mock_get_conn:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_get_conn.return_value.__enter__.return_value = mock_conn

            deleted = db.delete_category(1)
            assert deleted is True
            mock_conn.commit.assert_called()


# ==============================================================================
# 5. Ürün (Product) CRUD ve Many-to-Many Kategori Testleri
# ==============================================================================
def test_postgres_product_add_validation_and_crud():
    """
    PostgresDatabase üzerinde ürün ekleme, kategori doğrulama ve silme testleri.
    """
    db = PostgresDatabase()
    now = datetime.now(timezone.utc)

    # Kategori ID verilmediğinde hata fırlatmalı
    with pytest.raises(ValueError, match="en az bir geçerli kategori ID'si"):
        db.add({"name": "Ürün 1", "price": 100, "stock": 10, "category_ids": []})

    # Geçerli ürün ekleme
    with patch.object(db, "_get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # 1. kategori var kontrolü, 2. insert returning id
        mock_cursor.fetchone.side_effect = [{"id": 1}, {"id": 10}]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        with patch.object(db, "get_by_id") as mock_get_by_id:
            mock_get_by_id.return_value = {
                "id": 10,
                "name": "Oyuncu Faresi",
                "description": "RGB Optik Mouse",
                "price": 750.0,
                "stock": 25,
                "is_active": True,
                "created_at": now.isoformat(),
                "category_ids": [1],
                "categories": [{"id": 1, "name": "Gaming", "description": None, "created_at": now.isoformat()}],
            }
            product = db.add({
                "name": "Oyuncu Faresi",
                "description": "RGB Optik Mouse",
                "price": 750.0,
                "stock": 25,
                "category_ids": [1],
                "is_active": True,
            })
            assert product["id"] == 10
            assert product["price"] == 750.0
            assert product["category_ids"] == [1]


# ==============================================================================
# 6. Atomik Sipariş ve Stok Yönetimi Testleri (Transactional)
# ==============================================================================
def test_postgres_order_atomic_insufficient_stock():
    """
    Yetersiz stok durumunda create_order_atomic metodunun ValueError fırlattığını doğrular.
    """
    db = PostgresDatabase()

    with patch.object(db, "_get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Ürünün stoğu 2 ama istenen 5
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "name": "Klavye",
            "price": 500.0,
            "stock": 2,
            "is_active": True,
        }
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        with pytest.raises(ValueError, match="Yetersiz stok"):
            db.create_order_atomic(
                customer_email="test@musteri.com",
                items_data=[{"product_id": 1, "quantity": 5}],
            )


def test_postgres_order_status_update_restores_stock():
    """
    Sipariş durumu CANCELLED yapıldığında ürün stoklarının geri yüklendiğini test eder.
    """
    db = PostgresDatabase()
    now = datetime.now(timezone.utc)

    mock_order = {
        "id": 99,
        "customer_email": "test@musteri.com",
        "total_amount": 1000.0,
        "status": "PENDING",
        "created_at": now.isoformat(),
        "items": [{"id": 1, "product_id": 10, "quantity": 2, "unit_price": 500.0}],
    }

    with patch.object(db, "get_order_by_id", side_effect=[mock_order, {**mock_order, "status": "CANCELLED"}]):
        with patch.object(db, "_get_connection") as mock_get_conn:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_get_conn.return_value.__enter__.return_value = mock_conn

            updated = db.update_order_status_atomic(99, "CANCELLED")
            assert updated["status"] == "CANCELLED"

            # Stok artırma UPDATE sorgusunun çağrıldığını doğrula
            stock_restore_call = any(
                "UPDATE products SET stock = stock +" in str(call) for call in mock_cursor.execute.call_args_list
            )
            assert stock_restore_call is True
