"""
==============================================================================
SQLAlchemy Birleşik Veritabanı Adaptörü (Unified SqlAlchemy Database Adapter)
==============================================================================
Cosmic Python Repository Pattern standartlarında hem SQLite hem de PostgreSQL
ile çalışabilen ana adaptör sınıfı.
==============================================================================
"""

import os
import sys
import threading
from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from interfaces.repositories import (
    ICategoryRepository,
    IDatabase,
    IOrderRepository,
    IProductRepository,
)
from adapters.sqlalchemy.category_repository import SqlAlchemyCategoryRepository
from adapters.sqlalchemy.models import Base
from adapters.sqlalchemy.order_repository import SqlAlchemyOrderRepository
from adapters.sqlalchemy.product_repository import SqlAlchemyProductRepository


class SqlAlchemyDatabase(IDatabase):
    """
    SQLAlchemy altyapısını kullanarak SQLite veya PostgreSQL üzerinde
    IDatabase sözleşmesini eksiksiz yerine getiren ana veritabanı adaptörü.
    """

    def __init__(self, database_url: Optional[str] = None) -> None:
        if database_url:
            self.db_url = database_url
        else:
            db_type = os.getenv("DB_TYPE", "sqlite").lower().strip()
            is_testing = "pytest" in sys.modules

            if db_type in ("postgres", "postgresql"):
                host = os.getenv("POSTGRES_HOST", "localhost")
                port = os.getenv("POSTGRES_PORT", "5432")
                default_db = "test_proje_db" if is_testing else "proje_db"
                db_name = os.getenv("POSTGRES_DB", default_db)
                user = os.getenv("POSTGRES_USER", "postgres")
                password = os.getenv("POSTGRES_PASSWORD", "")
                
                auth = f"{user}:{password}@" if user or password else ""
                self.db_url = os.getenv("DATABASE_URL") or f"postgresql://{auth}{host}:{port}/{db_name}"
            else:
                db_file = "test_products.db" if is_testing else "products.db"
                self.db_url = f"sqlite:///./{db_file}"

        # Engine ve Session Yapılandırması
        connect_args = {"check_same_thread": False} if self.db_url.startswith("sqlite") else {}
        self.engine = create_engine(self.db_url, connect_args=connect_args, echo=False)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self._lock = threading.RLock()

        # Modüler Domain Repositories (Cosmic Python Composition)
        self._category_repo = SqlAlchemyCategoryRepository(self.session_factory)
        self._product_repo = SqlAlchemyProductRepository(self.session_factory)
        self._order_repo = SqlAlchemyOrderRepository(self.session_factory)

        # Tabloları oluştur
        self.init_db()

    def init_db(self) -> None:
        """Veritabanı tablolarını oluşturur."""
        try:
            Base.metadata.create_all(self.engine)
        except Exception:
            pass

    # ==============================================================================
    # 1. KATEGORİ REPOSITORY DELEGASYONLARI (ICategoryRepository)
    # ==============================================================================
    def add_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._category_repo.add_category(category_data)

    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        return self._category_repo.get_category_by_id(category_id)

    def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        return self._category_repo.get_category_by_name(name)

    def get_all_categories(self) -> List[Dict[str, Any]]:
        return self._category_repo.get_all_categories()

    def update_category(self, category_id: int, category_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._category_repo.update_category(category_id, category_data)

    def delete_category(self, category_id: int) -> bool:
        return self._category_repo.delete_category(category_id)

    # ==============================================================================
    # 2. ÜRÜN REPOSITORY DELEGASYONLARI (IProductRepository)
    # ==============================================================================
    def add(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._product_repo.add(product_data)

    def get_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        return self._product_repo.get_by_id(product_id)

    def get_all(self) -> List[Dict[str, Any]]:
        return self._product_repo.get_all()

    def update(self, product_id: int, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._product_repo.update(product_id, product_data)

    def patch(self, product_id: int, partial_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._product_repo.patch(product_id, partial_data)

    def delete(self, product_id: int) -> bool:
        return self._product_repo.delete(product_id)

    # ==============================================================================
    # 3. SİPARİŞ REPOSITORY DELEGASYONLARI (IOrderRepository)
    # ==============================================================================
    def create_order_atomic(self, customer_email: str, items_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self._order_repo.create_order_atomic(customer_email, items_data)

    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        return self._order_repo.get_order_by_id(order_id)

    def get_all_orders(
        self,
        customer_email: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self._order_repo.get_all_orders(customer_email, status)

    def update_order_status_atomic(self, order_id: int, new_status: str) -> Optional[Dict[str, Any]]:
        return self._order_repo.update_order_status_atomic(order_id, new_status)

    # ==============================================================================
    # 4. YARDIMCI VE TEST METOTLARI (CLEAR & SEED)
    # ==============================================================================
    def clear(self) -> None:
        """Tüm tablolardaki verileri temizler ve sequence sayaçlarını sıfırlar."""
        with self._lock:
            with self.session_factory() as session:
                if self.db_url.startswith("postgresql"):
                    session.execute(
                        text(
                            "TRUNCATE TABLE order_items, orders, product_categories, products, categories "
                            "RESTART IDENTITY CASCADE;"
                        )
                    )
                else:
                    session.execute(text("DELETE FROM order_items;"))
                    session.execute(text("DELETE FROM orders;"))
                    session.execute(text("DELETE FROM product_categories;"))
                    session.execute(text("DELETE FROM products;"))
                    session.execute(text("DELETE FROM categories;"))
                    try:
                        session.execute(text("DELETE FROM sqlite_sequence;"))
                    except Exception:
                        pass
                session.commit()

    def seed_initial_data(self) -> None:
        """Başlangıç kategorilerini ve örnek ürünleri yükler."""
        with self._lock:
            # 1. Eksik Kategorileri Ekle
            sample_categories = [
                {"name": "Elektronik", "description": "Bilgisayar, monitör, klavye ve teknolojik ürünler."},
                {"name": "Mobilya", "description": "Ergonomik çalışma koltukları ve ofis masaları."},
                {"name": "Ev & Yaşam", "description": "Termos, matara ve günlük yaşam gereçleri."},
                {"name": "Aksesuar", "description": "Klavye tuş takımları, fare altlıkları ve aparatlar."},
                {"name": "Gaming", "description": "Oyuncu ekipmanları, RGB aydınlatmalı profesyonel donanımlar."},
            ]

            for cat in sample_categories:
                if not self.get_category_by_name(cat["name"]):
                    self.add_category(cat)

            all_cats = self.get_all_categories()
            cat_map = {c["name"]: c["id"] for c in all_cats}

            # 2. Ürünler Boşsa Ekle
            if len(self.get_all()) > 0:
                return

            sample_products = [
                {
                    "name": "Kablosuz Mekanik Klavye",
                    "description": "RGB aydınlatmalı, Bluetooth & 2.4GHz bağlantılı mekanik klavye.",
                    "price": 1899.90,
                    "stock": 35,
                    "category_ids": [cat_map["Elektronik"], cat_map["Aksesuar"], cat_map["Gaming"]],
                    "is_active": True,
                },
                {
                    "name": "Ultra HD 4K Monitör 27 inç",
                    "description": "IPS panel, 144Hz yenileme hızı, HDR400 destekli profesyonel monitör.",
                    "price": 8450.00,
                    "stock": 12,
                    "category_ids": [cat_map["Elektronik"], cat_map["Gaming"]],
                    "is_active": True,
                },
                {
                    "name": "Ergonomik Ofis Koltuğu",
                    "description": "Bel desteği ayarlanabilir, nefes alabilen file kumaşlı çalışma koltuğu.",
                    "price": 4200.00,
                    "stock": 8,
                    "category_ids": [cat_map["Mobilya"], cat_map["Ev & Yaşam"]],
                    "is_active": True,
                },
                {
                    "name": "Paslanmaz Çelik Termos 750ml",
                    "description": "12 saat sıcak, 24 saat soğuk tutma kapasiteli çift cidarlı termos.",
                    "price": 650.00,
                    "stock": 50,
                    "category_ids": [cat_map["Ev & Yaşam"]],
                    "is_active": True,
                },
                {
                    "name": "Gürültü Engelleyici Kulaklık",
                    "description": "Aktif gürültü engelleme (ANC), 40 saat pil ömrü, Hi-Res ses sertifikalı.",
                    "price": 3150.00,
                    "stock": 0,
                    "category_ids": [cat_map["Elektronik"], cat_map["Aksesuar"]],
                    "is_active": False,
                },
            ]

            for item in sample_products:
                self.add(item)
