"""
==============================================================================
Veri Erişim Adaptörleri Paketi (Adapters Layer)
==============================================================================
Cosmic Python standartlarında, somut veri erişim adaptörleri:
- SqlAlchemyDatabase (SQLite ve PostgreSQL destekli birleşik adaptör)
- FakeRepository (In-Memory test adaptörü)
==============================================================================
"""

from adapters.sqlalchemy.database import SqlAlchemyDatabase
from adapters.sqlalchemy.category_repository import SqlAlchemyCategoryRepository
from adapters.sqlalchemy.product_repository import SqlAlchemyProductRepository
from adapters.sqlalchemy.order_repository import SqlAlchemyOrderRepository
from adapters.fake.fake_repository import FakeRepository

# Geriye dönük uyumluluk için alias
PostgresDatabase = SqlAlchemyDatabase

__all__ = [
    "SqlAlchemyDatabase",
    "SqlAlchemyCategoryRepository",
    "SqlAlchemyProductRepository",
    "SqlAlchemyOrderRepository",
    "FakeRepository",
    "PostgresDatabase",
]
