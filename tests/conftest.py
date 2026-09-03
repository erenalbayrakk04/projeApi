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
