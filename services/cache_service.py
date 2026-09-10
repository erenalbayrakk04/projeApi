"""
==============================================================================
Önbellekleme Servis Katmanı (Cache Service - Cache-Aside Pattern)
==============================================================================
Bu modül, veritabanı sorgularının sonuçlarını Redis üzerinde önbelleğe alır,
TTL (Time-To-Live) ile yönetir ve desen bazlı (pattern-based) önbellek
geçersiz kılma (cache invalidation) operasyonlarını yürütür.
==============================================================================
"""

import json
import logging
from typing import Any, Callable, Dict, List, Optional
from adapters.redis.redis_client import get_redis_client

logger = logging.getLogger("cache_service")


class CacheService:
    """
    Cache-Aside (Lazy Loading) önbellekleme stratejisini uygulayan servis sınıfı.
    """

    def __init__(self, default_ttl: int = 60, redis_client: Optional[Any] = None) -> None:
        self.default_ttl = default_ttl
        self._custom_client = redis_client
        self.hits = 0
        self.misses = 0

    @property
    def client(self) -> Any:
        if self._custom_client is not None:
            return self._custom_client
        return get_redis_client()

    def clear_all(self) -> int:
        """Tüm önbelleği temizler."""
        return self.delete_pattern("*")

    def get(self, key: str) -> Optional[Any]:
        """
        Önbellekten anahtara karşılık gelen veriyi JSON olarak okur ve çözümler.
        """
        try:
            raw = self.client.get(key)
            if raw is None:
                self.misses += 1
                logger.debug(f"[Cache MISS] Anahtar bulunamadı: {key}")
                return None

            self.hits += 1
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            logger.debug(f"[Cache HIT] Veri önbellekten alındı: {key}")
            return json.loads(raw)
        except Exception as e:
            logger.error(f"[Cache Error] get('{key}') başarısız: {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """
        Veriyi JSON formatında serileştirerek önbelleğe yazar.
        """
        try:
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            self.client.set(key, serialized, ex=ttl)
            logger.debug(f"[Cache SET] Anahtar kaydedildi: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"[Cache Error] set('{key}') başarısız: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Belirtilen tek bir anahtarı önbellekten siler.
        """
        try:
            res = self.client.delete(key)
            logger.debug(f"[Cache DELETE] Anahtar silindi: {key}")
            return bool(res)
        except Exception as e:
            logger.error(f"[Cache Error] delete('{key}') başarısız: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Belirli bir desene uyan tüm anahtarları topluca siler (örn: 'products:*').
        """
        try:
            keys = self.client.keys(pattern)
            if not keys:
                return 0

            # Bytes anahtarları string'e çevir
            str_keys = [k.decode("utf-8") if isinstance(k, bytes) else k for k in keys]
            deleted_count = self.client.delete(*str_keys)
            logger.info(f"🧹 [Cache Invalidation] '{pattern}' desenine uyan {deleted_count} anahtar temizlendi.")
            return deleted_count
        except Exception as e:
            logger.error(f"[Cache Error] delete_pattern('{pattern}') başarısız: {e}")
            return 0

    def get_or_set(
        self,
        key: str,
        factory_fn: Callable[[], Any],
        ttl_seconds: Optional[int] = None,
    ) -> Any:
        """
        Cache-Aside Pattern Yardımcısı:
        1. Önbellekte veri varsa doğrudan döner (Cache HIT).
        2. Yoksa (Cache MISS), `factory_fn` fonksiyonunu çalıştırıp sonucu veritabanından alır,
           önbelleğe yazar ve döner.
        """
        cached_data = self.get(key)
        if cached_data is not None:
            return cached_data

        # Veritabanından / kaynaktan hesapla
        fresh_data = factory_fn()

        # Sonucu önbelleğe kaydet
        if fresh_data is not None:
            self.set(key, fresh_data, ttl_seconds)

        return fresh_data

    # ==============================================================================
    # DOMAIN-SPECIFIC INVALIDATION HELPERS
    # ==============================================================================
    def invalidate_products(self) -> int:
        """Tüm ürün filtre ve liste önbelleklerini temizler."""
        return self.delete_pattern("products:*")

    def invalidate_categories(self) -> int:
        """Tüm kategori önbelleklerini temizler."""
        return self.delete_pattern("categories:*")

    def invalidate_orders(self) -> int:
        """Tüm sipariş önbelleklerini temizler."""
        return self.delete_pattern("orders:*")

    def get_stats(self) -> Dict[str, Any]:
        """Önbellek istatistiklerini döndürür."""
        is_fallback = "InMemory" in self.client.__class__.__name__
        try:
            total_keys = len(self.client.keys("*"))
        except Exception:
            total_keys = 0

        return {
            "driver": "In-Memory Fallback" if is_fallback else "Redis Server",
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": f"{(self.hits / (self.hits + self.misses) * 100):.1f}%" if (self.hits + self.misses) > 0 else "0%",
            "active_keys": total_keys,
        }


# Global Singleton Cache Servisi
cache_service = CacheService(default_ttl=60)
