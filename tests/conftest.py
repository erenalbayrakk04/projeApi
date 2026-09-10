"""
==============================================================================
Pytest Global Test Yapılandırması (Global Test Configuration & Fixtures)
==============================================================================
Bu modül, testler çalışırken izole SQLite test veritabanının kullanılmasını
ve her test öncesi/sonrası temizlenmesini garanti eder.
==============================================================================
"""

import os
# Test çalışırken izole SQLite test veritabanını kullan
os.environ["DB_TYPE"] = "sqlite"

import pytest
from database import db
from services.cache_service import cache_service
from events.base import event_bus
from events.observers import (
    CacheInvalidationObserver,
    StockAlertObserver,
    NotificationObserver,
    AuditLogObserver,
)


@pytest.fixture(autouse=True)
def reset_database_and_services():
    """
    Her test fonksiyonu çalışmadan önce ve çalıştıktan sonra
    aktif veritabanını, Redis/in-memory önbelleği ve Event Bus'ı temizler.
    """
    db.clear()
    db.seed_initial_data()
    cache_service.clear_all()
    event_bus.clear()

    # Varsayılan gözlemcileri kaydet
    event_bus.subscribe(CacheInvalidationObserver())
    event_bus.subscribe(StockAlertObserver(stock_threshold=10))
    event_bus.subscribe(NotificationObserver())
    event_bus.subscribe(AuditLogObserver())

    yield

    db.clear()
    cache_service.clear_all()
    event_bus.clear()

