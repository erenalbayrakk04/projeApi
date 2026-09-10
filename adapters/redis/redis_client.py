"""
==============================================================================
Redis İstemcisi ve Graceful Fallback Adaptörü (Redis Client & In-Memory Fallback)
==============================================================================
Bu modül, Redis bağlantısını yönetir. Eğer Redis sunucusuna erişilemezse
(örneğin lokal testler, CI/CD adımları veya geçici kesintiler) sistemin
asla çökmemesi için otomatik olarak thread-safe bellek içi (In-Memory)
önbellekleme adaptörüne geri döner (Graceful Degradation / Fallback).
==============================================================================
"""

import fnmatch
import logging
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("redis_client")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None  # type: ignore
    REDIS_AVAILABLE = False


class InMemoryCacheFallback:
    """
    Redis sunucusu kapalıyken veya mevcut değilken kullanılan
    thread-safe, TTL destekli bellek içi (In-Memory) sahte Redis adaptörü.
    """

    def __init__(self) -> None:
        self._store: Dict[str, bytes] = {}
        self._expiry: Dict[str, float] = {}
        self._lock = threading.RLock()
        logger.info("🧠 [InMemoryCacheFallback] Bellek içi önbellek adaptörü başlatıldı.")

    def ping(self) -> bool:
        return True

    def get(self, name: str) -> Optional[bytes]:
        with self._lock:
            now = time.time()
            if name in self._expiry and self._expiry[name] < now:
                # Süresi dolmuş
                del self._store[name]
                del self._expiry[name]
                return None
            return self._store.get(name)

    def set(self, name: str, value: Union[str, bytes], ex: Optional[int] = None) -> bool:
        with self._lock:
            val_bytes = value.encode("utf-8") if isinstance(value, str) else value
            self._store[name] = val_bytes
            if ex is not None:
                self._expiry[name] = time.time() + ex
            elif name in self._expiry:
                del self._expiry[name]
            return True

    def delete(self, *names: str) -> int:
        count = 0
        with self._lock:
            for name in names:
                if name in self._store:
                    del self._store[name]
                    if name in self._expiry:
                        del self._expiry[name]
                    count += 1
        return count

    def keys(self, pattern: str = "*") -> List[bytes]:
        with self._lock:
            now = time.time()
            # Önce süresi dolanları temizle
            expired_keys = [k for k, exp in self._expiry.items() if exp < now]
            for k in expired_keys:
                if k in self._store:
                    del self._store[k]
                del self._expiry[k]

            matched = []
            for k in self._store.keys():
                if fnmatch.fnmatch(k, pattern):
                    matched.append(k.encode("utf-8"))
            return matched

    def flushall(self) -> bool:
        with self._lock:
            self._store.clear()
            self._expiry.clear()
        return True


_redis_client_instance: Optional[Any] = None
_client_lock = threading.RLock()


def get_redis_client() -> Any:
    """
    Redis bağlantı istemcisini döndürür.
    Bağlantı kurulamazsa InMemoryCacheFallback nesnesini döndürür.
    """
    global _redis_client_instance

    with _client_lock:
        if _redis_client_instance is not None:
            return _redis_client_instance

        # Test ortamındaysak ve REDIS_FORCE_REAL ayarlanmamışsa in-memory fallback kullan
        is_testing = "pytest" in sys.modules
        force_real = os.getenv("REDIS_FORCE_REAL", "").lower() in ("1", "true")

        if is_testing and not force_real:
            _redis_client_instance = InMemoryCacheFallback()
            return _redis_client_instance

        if not REDIS_AVAILABLE:
            logger.warning("⚠️ 'redis' kütüphanesi bulunamadı. InMemoryCacheFallback kullanılıyor.")
            _redis_client_instance = InMemoryCacheFallback()
            return _redis_client_instance

        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))
        password = os.getenv("REDIS_PASSWORD") or None
        db_num = int(os.getenv("REDIS_DB", "0"))

        try:
            client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=db_num,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
                decode_responses=False,
            )
            # Bağlantıyı test et
            client.ping()
            logger.info(f"✅ [Redis] Redis sunucusuna başarıyla bağlanıldı ({host}:{port} - DB {db_num}).")
            _redis_client_instance = client
        except Exception as e:
            logger.warning(
                f"⚠️ [Redis] Redis sunucusuna bağlanılamadı ({host}:{port}): {e}. "
                f"Sistem bellek içi InMemoryCacheFallback ile çalışmaya devam ediyor."
            )
            _redis_client_instance = InMemoryCacheFallback()

        return _redis_client_instance


def reset_redis_client() -> None:
    """İstemci örneğini sıfırlar (testler ve yeniden başlatma için)."""
    global _redis_client_instance
    with _client_lock:
        _redis_client_instance = None
