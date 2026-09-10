"""
==============================================================================
Redis & In-Memory Cache Layer Unit & Integration Tests
==============================================================================
Bu modül, Cache-Aside stratejisini, TTL sürelerini, pattern bazlı cache
temizlemeyi ve domain event tetiklendiğinde otomatik cache invalidation'ı test eder.
==============================================================================
"""

import time
import pytest
from services.cache_service import CacheService
from adapters.redis.redis_client import InMemoryCacheFallback
from services.product_service import ProductService
from services.category_service import CategoryService
from schemas.product import ProductCreate, ProductUpdate
from schemas.category import CategoryCreate


def test_in_memory_cache_fallback_basic_operations():
    """Fallback cache mekanizmasının get, set, delete ve ttl desteğini test eder."""
    cache = InMemoryCacheFallback()

    # 1. Set and Get (returns bytes matching Redis behaviour)
    assert cache.set("test:key1", "Laptop", ex=60) is True
    assert cache.get("test:key1") == b"Laptop"

    # 2. Delete
    assert cache.delete("test:key1") == 1
    assert cache.get("test:key1") is None

    # 3. Non-existent key
    assert cache.get("test:non_existent") is None


def test_in_memory_cache_expiration():
    """Önbelleğin TTL süresi dolunca veriyi sildiğini test eder."""
    cache = InMemoryCacheFallback()
    cache.set("test:short_lived", "data", ex=1)  # 1 saniye TTL
    assert cache.get("test:short_lived") == b"data"

    time.sleep(1.2)
    assert cache.get("test:short_lived") is None


def test_cache_service_get_or_set_cache_hit():
    """Cache-Aside get_or_set mekanizmasında cache HIT durumunu doğrular."""
    backend = InMemoryCacheFallback()
    service = CacheService(redis_client=backend)

    call_count = 0
    def expensive_query():
        nonlocal call_count
        call_count += 1
        return {"data": "expensive_result"}

    # 1. İlk Çağrı (Cache MISS) -> Fonksiyon çalışmalı
    res1 = service.get_or_set("query:key", expensive_query, ttl_seconds=60)
    assert res1 == {"data": "expensive_result"}
    assert call_count == 1

    # 2. İkinci Çağrı (Cache HIT) -> Fonksiyon ÇALIŞMAMALI, cache'ten gelmeli
    res2 = service.get_or_set("query:key", expensive_query, ttl_seconds=60)
    assert res2 == {"data": "expensive_result"}
    assert call_count == 1  # call_count artmamalı!


def test_cache_service_delete_pattern():
    """delete_pattern ile glob pattern eşleşen tüm keylerin silindiğini test eder."""
    backend = InMemoryCacheFallback()
    service = CacheService(redis_client=backend)

    service.set("products:item:1", {"id": 1})
    service.set("products:item:2", {"id": 2})
    service.set("products:list:1", [{"id": 1}])
    service.set("categories:item:1", {"id": 1})

    # products:* kalıbını sil
    deleted_count = service.delete_pattern("products:*")
    assert deleted_count == 3
    assert service.get("products:item:1") is None
    assert service.get("products:item:2") is None
    assert service.get("products:list:1") is None
    assert service.get("categories:item:1") is not None  # Kategori kalmalı


def test_product_service_cache_invalidation_on_mutation():
    """Ürün güncellendiğinde veya silindiğinde observer ile önbelleğin otomatik temizlendiğini test eder."""
    prod_service = ProductService()

    # 1. Ürünleri listele -> Cache'e kaydedilsin
    list1 = prod_service.get_products()
    assert len(list1) > 0

    # Cache'te veri olduğunu doğrula
    assert prod_service.cache.get("products:list:cat=None:cat_id=None:min=None:max=None:active=None:skip=0:limit=10") is not None

    # 2. Yeni ürün ekle -> ProductCreatedEvent -> CacheInvalidationObserver -> products:* silinmeli
    new_prod = prod_service.create_product(
        ProductCreate(name="Önbellek Test Ürünü", price=99.0, stock=10, category_ids=[1])
    )

    # Cache temizlenmiş olmalı
    assert prod_service.cache.get("products:list:cat=None:cat_id=None:min=None:max=None:active=None:skip=0:limit=10") is None

    # Tekrar listele -> Yeni ürün görünmeli
    list2 = prod_service.get_products()
    ids = [p.id for p in list2]
    assert new_prod.id in ids
