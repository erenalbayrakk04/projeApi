"""
==============================================================================
Pytest Global Test Yapılandırması (Global Test Configuration & Fixtures)
==============================================================================
Bu modül, testler çalışırken veritabanının (SQLite veya PostgreSQL)
her test öncesinde ve sonrasında izole edilmesini, temizlenmesini ve
seed verilerinin tutarlı şekilde yeniden yüklenmesini garanti eder.
==============================================================================
"""

import pytest
from database import db


@pytest.fixture(autouse=True)
def reset_database():
    """
    Her test fonksiyonu çalışmadan önce ve çalıştıktan sonra
    aktif veritabanını temizler ve seed verilerini yükler.
    """
    db.clear()
    db.seed_initial_data()
    yield
    db.clear()
