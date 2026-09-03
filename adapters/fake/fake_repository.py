"""
==============================================================================
Cosmic Python Sahte Bellek İçi Depo (Fake In-Memory Repository)
==============================================================================
Cosmic Python Chapter 02 standardında, testlerin veritabanına bağlanmadan
milisaniyeler içinde çalışmasını sağlayan in-memory sahte depo implementasyonu.
==============================================================================
"""

from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional

from interfaces.repositories import IDatabase


class FakeRepository(IDatabase):
    """
    Herhangi bir veritabanı veya I/O gerektirmeyen, tamamen Python bellek
    yapılarını (dict/list) kullanan test deposu.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._categories: Dict[int, Dict[str, Any]] = {}
        self._products: Dict[int, Dict[str, Any]] = {}
        self._orders: Dict[int, Dict[str, Any]] = {}
        self._cat_seq = 1
        self._prod_seq = 1
        self._order_seq = 1

    # ==============================================================================
    # 1. KATEGORİ METOTLARI
    # ==============================================================================
    def add_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            name = category_data["name"].strip()
            for c in self._categories.values():
                if c["name"].lower() == name.lower():
                    raise ValueError(f"'{name}' isimli bir kategori zaten mevcut.")

            cat_id = self._cat_seq
            self._cat_seq += 1

            cat = {
                "id": cat_id,
                "name": name,
                "description": category_data.get("description"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._categories[cat_id] = cat
            return dict(cat)

    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            cat = self._categories.get(category_id)
            return dict(cat) if cat else None

    def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            clean_name = name.strip().lower()
            for cat in self._categories.values():
                if cat["name"].lower() == clean_name:
                    return dict(cat)
            return None

    def get_all_categories(self) -> List[Dict[str, Any]]:
        with self._lock:
            return sorted([dict(c) for c in self._categories.values()], key=lambda x: x["id"])

    def update_category(self, category_id: int, category_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            cat = self._categories.get(category_id)
            if not cat:
                return None
            cat["name"] = category_data["name"].strip()
            if "description" in category_data:
                cat["description"] = category_data["description"]
            return dict(cat)

    def delete_category(self, category_id: int) -> bool:
        with self._lock:
            if category_id in self._categories:
                del self._categories[category_id]
                return True
            return False

    # ==============================================================================
    # 2. ÜRÜN METOTLARI
    # ==============================================================================
    def add(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            category_ids = product_data.get("category_ids", [])
            categories = []
            for cid in category_ids:
                cat = self._categories.get(cid)
                if not cat:
                    raise ValueError(f"Belirtilen kategori bulunamadı: {cid}")
                categories.append(dict(cat))

            prod_id = self._prod_seq
            self._prod_seq += 1

            product = {
                "id": prod_id,
                "name": product_data["name"].strip(),
                "description": product_data.get("description"),
                "price": float(product_data["price"]),
                "stock": int(product_data["stock"]),
                "is_active": bool(product_data.get("is_active", True)),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "category_ids": [c["id"] for c in categories],
                "categories": categories,
            }
            self._products[prod_id] = product
            return dict(product)

    def get_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            prod = self._products.get(product_id)
            return dict(prod) if prod else None

    def get_all(self) -> List[Dict[str, Any]]:
        with self._lock:
            return sorted([dict(p) for p in self._products.values()], key=lambda x: x["id"])

    def update(self, product_id: int, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            prod = self._products.get(product_id)
            if not prod:
                return None

            category_ids = product_data.get("category_ids", [])
            categories = []
            for cid in category_ids:
                cat = self._categories.get(cid)
                if not cat:
                    raise ValueError(f"Belirtilen kategori bulunamadı: {cid}")
                categories.append(dict(cat))

            prod["name"] = product_data["name"].strip()
            prod["description"] = product_data.get("description")
            prod["price"] = float(product_data["price"])
            prod["stock"] = int(product_data["stock"])
            prod["is_active"] = bool(product_data.get("is_active", True))
            prod["category_ids"] = [c["id"] for c in categories]
            prod["categories"] = categories
            return dict(prod)

    def patch(self, product_id: int, partial_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            prod = self._products.get(product_id)
            if not prod:
                return None

            if "name" in partial_data:
                prod["name"] = partial_data["name"].strip()
            if "description" in partial_data:
                prod["description"] = partial_data["description"]
            if "price" in partial_data:
                prod["price"] = float(partial_data["price"])
            if "stock" in partial_data:
                prod["stock"] = int(partial_data["stock"])
            if "is_active" in partial_data:
                prod["is_active"] = bool(partial_data["is_active"])
            if "category_ids" in partial_data:
                category_ids = partial_data["category_ids"]
                categories = []
                for cid in category_ids:
                    cat = self._categories.get(cid)
                    if not cat:
                        raise ValueError(f"Belirtilen kategori bulunamadı: {cid}")
                    categories.append(dict(cat))
                prod["category_ids"] = [c["id"] for c in categories]
                prod["categories"] = categories
            return dict(prod)

    def delete(self, product_id: int) -> bool:
        with self._lock:
            if product_id in self._products:
                del self._products[product_id]
                return True
            return False

    # ==============================================================================
    # 3. SİPARİŞ METOTLARI
    # ==============================================================================
    def create_order_atomic(
        self,
        customer_email: str,
        items_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        with self._lock:
            total_amount = 0.0
            order_items = []

            for idx, item in enumerate(items_data, start=1):
                prod_id = item["product_id"]
                req_qty = item["quantity"]

                prod = self._products.get(prod_id)
                if not prod:
                    raise ValueError(f"ID'si {prod_id} olan ürün bulunamadı.")
                if not prod["is_active"]:
                    raise ValueError(f"'{prod['name']}' ürünü satışta/aktif değildir.")
                if prod["stock"] < req_qty:
                    raise ValueError(
                        f"'{prod['name']}' için Yetersiz stok. Mevcut: {prod['stock']}, Talep: {req_qty}"
                    )

                unit_price = prod["price"]
                total_amount += unit_price * req_qty
                prod["stock"] -= req_qty

                order_items.append({
                    "id": idx,
                    "product_id": prod_id,
                    "quantity": req_qty,
                    "unit_price": unit_price,
                })

            order_id = self._order_seq
            self._order_seq += 1

            order = {
                "id": order_id,
                "customer_email": customer_email.strip(),
                "total_amount": round(total_amount, 2),
                "status": "PENDING",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "items": order_items,
            }
            self._orders[order_id] = order
            return dict(order)

    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            ord_ = self._orders.get(order_id)
            return dict(ord_) if ord_ else None

    def get_all_orders(
        self,
        customer_email: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            res = list(self._orders.values())
            if customer_email:
                res = [o for o in res if o["customer_email"].lower() == customer_email.strip().lower()]
            if status:
                res = [o for o in res if o["status"].upper() == status.strip().upper()]
            return sorted([dict(o) for o in res], key=lambda x: x["id"], reverse=True)

    def update_order_status_atomic(self, order_id: int, new_status: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            order = self._orders.get(order_id)
            if not order:
                return None

            prev = order["status"]
            target = new_status.strip().upper()

            if prev == target:
                return dict(order)

            if target == "CANCELLED" and prev != "CANCELLED":
                for it in order["items"]:
                    p = self._products.get(it["product_id"])
                    if p:
                        p["stock"] += it["quantity"]
            elif prev == "CANCELLED" and target != "CANCELLED":
                for it in order["items"]:
                    p = self._products.get(it["product_id"])
                    if not p or p["stock"] < it["quantity"]:
                        stk = p["stock"] if p else 0
                        raise ValueError(
                            f"Stok yetersizliği nedeniyle sipariş iptalden çıkartılamıyor: "
                            f"'{p['name'] if p else 'Ürün'}' için mevcut stok {stk}, "
                            f"gerekli adet {it['quantity']}."
                        )
                    p["stock"] -= it["quantity"]

            order["status"] = target
            return dict(order)

    def clear(self) -> None:
        with self._lock:
            self._categories.clear()
            self._products.clear()
            self._orders.clear()
            self._cat_seq = 1
            self._prod_seq = 1
            self._order_seq = 1

    def seed_initial_data(self) -> None:
        with self._lock:
            if self._categories or self._products:
                return

            cats = [
                {"name": "Elektronik", "description": "Bilgisayar, monitör, klavye ve teknolojik ürünler."},
                {"name": "Mobilya", "description": "Ergonomik çalışma koltukları ve ofis masaları."},
                {"name": "Ev & Yaşam", "description": "Termos, matara ve günlük yaşam gereçleri."},
                {"name": "Aksesuar", "description": "Klavye tuş takımları, fare altlıkları ve aparatlar."},
                {"name": "Gaming", "description": "Oyuncu ekipmanları, RGB aydınlatmalı profesyonel donanımlar."},
            ]
            for c in cats:
                self.add_category(c)

            all_c = self.get_all_categories()
            c_map = {c["name"]: c["id"] for c in all_c}

            prods = [
                {
                    "name": "Kablosuz Mekanik Klavye",
                    "description": "RGB aydınlatmalı, Bluetooth & 2.4GHz bağlantılı mekanik klavye.",
                    "price": 1899.90,
                    "stock": 35,
                    "category_ids": [c_map["Elektronik"], c_map["Aksesuar"], c_map["Gaming"]],
                    "is_active": True,
                },
                {
                    "name": "Ultra HD 4K Monitör 27 inç",
                    "description": "IPS panel, 144Hz yenileme hızı, HDR400 destekli profesyonel monitör.",
                    "price": 8450.00,
                    "stock": 12,
                    "category_ids": [c_map["Elektronik"], c_map["Gaming"]],
                    "is_active": True,
                },
                {
                    "name": "Ergonomik Ofis Koltuğu",
                    "description": "Bel desteği ayarlanabilir, nefes alabilen file kumaşlı çalışma koltuğu.",
                    "price": 4200.00,
                    "stock": 8,
                    "category_ids": [c_map["Mobilya"], c_map["Ev & Yaşam"]],
                    "is_active": True,
                },
                {
                    "name": "Paslanmaz Çelik Termos 750ml",
                    "description": "12 saat sıcak, 24 saat soğuk tutma kapasiteli çift cidarlı termos.",
                    "price": 650.00,
                    "stock": 50,
                    "category_ids": [c_map["Ev & Yaşam"]],
                    "is_active": True,
                },
                {
                    "name": "Gürültü Engelleyici Kulaklık",
                    "description": "Aktif gürültü engelleme (ANC), 40 saat pil ömrü, Hi-Res ses sertifikalı.",
                    "price": 3150.00,
                    "stock": 0,
                    "category_ids": [c_map["Elektronik"], c_map["Aksesuar"]],
                    "is_active": False,
                },
            ]
            for p in prods:
                self.add(p)
