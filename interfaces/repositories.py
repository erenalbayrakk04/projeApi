"""
==============================================================================
Soyut Veritabanı ve Depo Arayüzleri (Abstract Repository / Database Interfaces)
==============================================================================
Bu modül, SOLID prensiplerinden:
- Dependency Inversion Principle (DIP): Yüksek seviyeli servisler düşük seviyeli
  veritabanı sınıflarına değil, soyut arayüzlere bağımlı olmalıdır.
- Interface Segregation Principle (ISP): Her servis yalnızca ihtiyaç duyduğu
  metotları içeren arayüze bağımlı olmalıdır.
prensiplerine uygun olarak soyut arayüzleri tanımlar.
==============================================================================
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IProductRepository(ABC):
    """
    Ürün (Product) veri erişim operasyonları için soyut arayüz.
    """

    @abstractmethod
    def add(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Yeni bir ürün kaydeder."""
        pass

    @abstractmethod
    def get_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """ID numarasına göre ürünü getirir."""
        pass

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Tüm ürünleri listeler."""
        pass

    @abstractmethod
    def update(self, product_id: int, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mevcut bir ürünü baştan sona (PUT) günceller."""
        pass

    @abstractmethod
    def patch(self, product_id: int, partial_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mevcut bir ürünü kısmi olarak (PATCH) günceller."""
        pass

    @abstractmethod
    def delete(self, product_id: int) -> bool:
        """Ürünü siler."""
        pass


class ICategoryRepository(ABC):
    """
    Kategori (Category) veri erişim operasyonları için soyut arayüz.
    """

    @abstractmethod
    def add_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Yeni bir kategori kaydeder."""
        pass

    @abstractmethod
    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """ID numarasına göre kategori getirir."""
        pass

    @abstractmethod
    def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """İsme göre kategori arar."""
        pass

    @abstractmethod
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Tüm kategorileri listeler."""
        pass

    @abstractmethod
    def update_category(self, category_id: int, category_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Kategoriyi günceller."""
        pass

    @abstractmethod
    def delete_category(self, category_id: int) -> bool:
        """Kategoriyi siler."""
        pass


class IOrderRepository(ABC):
    """
    Sipariş (Order) veri erişim operasyonları için soyut arayüz.
    """

    @abstractmethod
    def create_order_atomic(self, customer_email: str, items_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Atomik sipariş oluşturur ve stokları günceller."""
        pass

    @abstractmethod
    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """ID numarasına göre siparişi getirir."""
        pass

    @abstractmethod
    def get_all_orders(
        self,
        customer_email: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Siparişleri listeler ve filtreler."""
        pass

    @abstractmethod
    def update_order_status_atomic(self, order_id: int, new_status: str) -> Optional[Dict[str, Any]]:
        """Sipariş durumunu atomik günceller ve iptal halinde stoğu iade eder."""
        pass


class IDatabase(IProductRepository, ICategoryRepository, IOrderRepository, ABC):
    """
    Tüm repository arayüzlerini birleştiren ana veritabanı arayüzü.
    """

    @abstractmethod
    def clear(self) -> None:
        """Tüm tabloları temizler."""
        pass

    @abstractmethod
    def seed_initial_data(self) -> None:
        """Başlangıç seed verilerini yükler."""
        pass
