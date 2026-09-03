"""
==============================================================================
Geriye Dönük Uyumluluk Modülü (PostgresDatabase Alias)
==============================================================================
Cosmic Python standartlarında birleştirilmiş SQLAlchemy adaptörünü dışa aktarır.
==============================================================================
"""

from adapters.sqlalchemy.database import SqlAlchemyDatabase as PostgresDatabase

__all__ = ["PostgresDatabase"]
