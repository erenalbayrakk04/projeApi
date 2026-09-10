"""
==============================================================================
Observer Pattern & Event Bus Temel Katmanı (Base Event & Observer Architecture)
==============================================================================
Bu modül, GoF (Gang of Four) Observer Pattern standartlarına uygun olarak
Event, Observer ve thread-safe EventPublisher (Event Bus) sınıflarını tanımlar.
==============================================================================
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional, Type
import uuid

logger = logging.getLogger("events")


@dataclass
class Event:
    """
    Sistemde meydana gelen bir olayı (Domain Event) temsil eden temel sınıf.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_name(self) -> str:
        """Olay sınıfının adını döndürür."""
        return self.__class__.__name__


class Observer(ABC):
    """
    Belirli olayları dinleyen ve tepki veren Gözlemci (Observer / Subscriber)
    soyut arayüzü.
    """

    @abstractmethod
    def handle(self, event: Event) -> None:
        """
        Olay meydana geldiğinde çalıştırılacak iş mantığı.
        """
        pass


class EventPublisher:
    """
    Olayları gözlemcilere (Observers) dağıtan, thread-safe Event Bus / Subject sınıfı.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._subscribers: Dict[Type[Event], List[Observer]] = {}
        self._global_subscribers: List[Observer] = []

    def subscribe(self, event_type_or_observer: Any, observer: Optional[Observer] = None) -> None:
        """
        Gözlemci kaydeder.
        Kullanım:
        1. `event_bus.subscribe(observer)` -> Tüm olaylara abone yapar (subscribe_all).
        2. `event_bus.subscribe(ProductCreatedEvent, observer)` -> Belirli olay türüne abone yapar.
        """
        with self._lock:
            if observer is None and isinstance(event_type_or_observer, Observer):
                self.subscribe_all(event_type_or_observer)
            elif observer is not None and issubclass(event_type_or_observer, Event):
                event_type = event_type_or_observer
                if event_type not in self._subscribers:
                    self._subscribers[event_type] = []
                if observer not in self._subscribers[event_type]:
                    self._subscribers[event_type].append(observer)
                    logger.debug(f"[EventPublisher] {observer.__class__.__name__} -> {event_type.__name__} abonesi oldu.")

    def subscribe_all(self, observer: Observer) -> None:
        """
        Tüm olay türlerini dinleyecek genel bir gözlemci (örn: AuditLogObserver) kaydeder.
        """
        with self._lock:
            if observer not in self._global_subscribers:
                self._global_subscribers.append(observer)
                logger.debug(f"[EventPublisher] {observer.__class__.__name__} tüm olaylara abone oldu.")

    @property
    def observer_count(self) -> int:
        """Kayıtlı benzersiz gözlemci sayısını döndürür."""
        with self._lock:
            all_obs = set(self._global_subscribers)
            for obs_list in self._subscribers.values():
                all_obs.update(obs_list)
            return len(all_obs)

    def unsubscribe(self, event_type: Type[Event], observer: Observer) -> None:
        """
        Bir gözlemcinin aboneliğini iptal eder.
        """
        with self._lock:
            if event_type in self._subscribers and observer in self._subscribers[event_type]:
                self._subscribers[event_type].remove(observer)

    def unsubscribe_all(self, observer: Observer) -> None:
        """
        Genel gözlemci aboneliğini iptal eder.
        """
        with self._lock:
            if observer in self._global_subscribers:
                self._global_subscribers.remove(observer)
            for event_type, observers in self._subscribers.items():
                if observer in observers:
                    observers.remove(observer)

    def publish(self, event: Event) -> None:
        """
        Bir olayı yayınlar ve ilgili tüm gözlemcileri tetikler.
        Bir gözlemcide hata çıkması diğer gözlemcileri veya ana akışı bozmaz (Fault-tolerant).
        """
        with self._lock:
            event_type = type(event)
            target_observers = list(self._subscribers.get(event_type, []))
            target_observers.extend([obs for obs in self._global_subscribers if obs not in target_observers])

        logger.info(f"📢 [EventPublished] {event.event_name} (ID: {event.event_id[:8]}) -> {len(target_observers)} gözlemciye iletiliyor.")

        for observer in target_observers:
            try:
                observer.handle(event)
            except Exception as e:
                logger.error(
                    f"❌ [ObserverError] {observer.__class__.__name__}, {event.event_name} olayını işlerken hata aldı: {e}",
                    exc_info=True,
                )

    def clear(self) -> None:
        """Tüm aboneleri temizler (özellikle birim testler için)."""
        with self._lock:
            self._subscribers.clear()
            self._global_subscribers.clear()


# Global Singleton Event Bus Nesnesi
event_bus = EventPublisher()
