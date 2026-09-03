"""
==============================================================================
Veritabanı Katmanı ve Fabrikası (Database Layer & Factory)
==============================================================================
Cosmic Python Repository Pattern standartlarında veritabanı sağlayıcısı.
FastAPI Dependency Injection ile servis katmanına soyut IDatabase arayüzünü
sağlar.
==============================================================================
"""

import os
from typing import Any, Optional

from interfaces.repositories import (
    ICategoryRepository,
    IDatabase,
    IOrderRepository,
    IProductRepository,
)
from adapters.sqlalchemy.database import SqlAlchemyDatabase
from adapters.fake.fake_repository import FakeRepository

# Geriye dönük uyumluluk için alias tanımları
SQLiteDatabase = SqlAlchemyDatabase
PostgresDatabase = SqlAlchemyDatabase

_active_database_instance: Optional[IDatabase] = None


def get_database() -> IDatabase:
    """
    FastAPI Dependency Injection için veritabanı fabrika (Factory) fonksiyonu.
    DB_TYPE çevre değişkenine göre uygun IDatabase adaptörünü sağlar:
    - DB_TYPE=sqlite (varsayılan): SQLite üzerinde çalışan SqlAlchemyDatabase.
    - DB_TYPE=postgres: PostgreSQL üzerinde çalışan SqlAlchemyDatabase.
    - DB_TYPE=fake: Tamamen bellek içi test için FakeRepository.
    """
    global _active_database_instance
    db_type = os.getenv("DB_TYPE", "sqlite").strip().lower()

    if _active_database_instance is None:
        if db_type == "fake":
            _active_database_instance = FakeRepository()
        else:
            _active_database_instance = SqlAlchemyDatabase()

    return _active_database_instance


class _DatabaseProxy:
    """
    Geriye dönük uyumluluk amacıyla db nesnesine yapılan doğrudan çağrıları
    aktif veritabanı adaptörüne dinamik yönlendirir.
    """

    def __getattr__(self, name: str) -> Any:
        return getattr(get_database(), name)

    def __repr__(self) -> str:
        return f"<DatabaseProxy active_adapter={get_database().__class__.__name__}>"


# Global dinamik veritabanı nesnesi (Singleton Proxy)
db: IDatabase = _DatabaseProxy()  # type: ignore

__all__ = [
    "IDatabase",
    "IProductRepository",
    "ICategoryRepository",
    "IOrderRepository",
    "SqlAlchemyDatabase",
    "SQLiteDatabase",
    "PostgresDatabase",
    "FakeRepository",
    "get_database",
    "db",
]
