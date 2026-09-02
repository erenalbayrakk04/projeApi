"""
==============================================================================
SQLite Veritabanı Modülü (Thread-Safe SQLite Database Module)
==============================================================================
Bu modül, verileri yerel bir SQLite veritabanı dosyasında (products.db)
saklayan thread-safe bir veri erişim katmanı sağlar.

Kapsanan Varlıklar ve İlişkiler (Entities & Relationships):
1. Ürünler (products)
2. Kategoriler (categories)
3. Ürün-Kategori Çoka-Çok İlişki Tablosu (product_categories - Many-to-Many)
4. Siparişler (orders)
5. Sipariş Kalemleri (order_items)

Test ortamı tespit edildiğinde otomatik olarak 'test_products.db' kullanılır.
==============================================================================
"""

import os
import sys
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from interfaces.repositories import IDatabase


class SQLiteDatabase(IDatabase):
    """
    Ürün, Kategori, Çoka-Çok Kategori İlişkisi ve Sipariş verilerini SQLite
    üzerinde saklayan, sorgulayan ve güncelleyen thread-safe veritabanı sınıfı.
    IDatabase soyut arayüzünü (Interface) somutlaştırır (Concrete Implementation).
    """

    def __init__(self, db_path: str = "products.db") -> None:
        """
        Veritabanı sınıfının kurucu metodu (Constructor).
        Sistem test ortamındaysa (pytest) otomatik olarak test veri tabanını kullanır.
        """
        # Eğer pytest çalışıyorsa test veri tabanını kullan
        is_testing = "pytest" in sys.modules
        self.db_path = "test_products.db" if is_testing else db_path

        # Eşzamanlı işlemleri sıraya sokan Mutex (Mutual Exclusion) kilidi (Re-entrant)
        self._lock: threading.RLock = threading.RLock()

        # Tabloları oluştur
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Veritabanına yeni bir bağlantı açar ve satırları dict benzeri erişim için yapılandırır.
        Foreign key (Yabancı Anahtar) desteğini açar.
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # SQLite'ta foreign key kısıtlamalarını aktif hale getir
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        """
        Gerekli tabloları (products, categories, product_categories, orders, order_items) oluşturur.
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Eski şema kontrolü: Eğer products tablosunda eski 'category' kolonu varsa tabloları yenile
                existing_cols = [
                    row[1] for row in cursor.execute("PRAGMA table_info(products)").fetchall()
                ]
                if "category" in existing_cols:
                    cursor.execute("DROP TABLE IF EXISTS product_categories")
                    cursor.execute("DROP TABLE IF EXISTS order_items")
                    cursor.execute("DROP TABLE IF EXISTS orders")
                    cursor.execute("DROP TABLE IF EXISTS products")

                # 1. Kategoriler Tablosu
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        created_at TEXT NOT NULL
                    )
                """)

                # 2. Ürünler Tablosu (Many-to-Many kategori yapısına uygun)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        price REAL NOT NULL,
                        stock INTEGER NOT NULL,
                        is_active INTEGER NOT NULL DEFAULT 1,
                        created_at TEXT NOT NULL
                    )
                """)

                # 3. Ürün-Kategori Ara Tablosu (Junction Table: Many-to-Many İlişki)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS product_categories (
                        product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                        category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
                        PRIMARY KEY (product_id, category_id)
                    )
                """)

                # 4. Siparişler Tablosu
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_email TEXT NOT NULL,
                        total_amount REAL NOT NULL,
                        status TEXT NOT NULL DEFAULT 'PENDING',
                        created_at TEXT NOT NULL
                    )
                """)

                # 5. Sipariş Kalemleri Tablosu
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS order_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                        product_id INTEGER NOT NULL REFERENCES products(id),
                        quantity INTEGER NOT NULL,
                        unit_price REAL NOT NULL
                    )
                """)

                conn.commit()

    # ==============================================================================
    # KATEGORİ (CATEGORY) VERİTABANI İŞLEMLERİ
    # ==============================================================================
    def _category_row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Kategori SQLite Row nesnesini Python sözlüğüne dönüştürür.
        """
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "created_at": datetime.fromisoformat(row["created_at"])
        }

    def add_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Yeni bir kategori kaydeder.
        """
        with self._lock:
            now = datetime.now(timezone.utc).isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO categories (name, description, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (
                        category_data["name"],
                        category_data.get("description"),
                        now
                    )
                )
                new_id = cursor.lastrowid
                conn.commit()

            result = self.get_category_by_id(new_id)
            if not result:
                raise RuntimeError("Kategori kaydedildi ancak geri okunurken hata oluştu.")
            return result

    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """ID'ye göre kategori getirir."""
        with self._lock:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM categories WHERE id = ?", (category_id,)
                ).fetchone()
                if row:
                    return self._category_row_to_dict(row)
                return None

    def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """İsme göre kategori getirir (Büyük/küçük harf duyarsız)."""
        with self._lock:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM categories WHERE LOWER(name) = LOWER(?)", (name.strip(),)
                ).fetchone()
                if row:
                    return self._category_row_to_dict(row)
                return None

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Tüm kategorileri listeler."""
        with self._lock:
            with self._get_connection() as conn:
                rows = conn.execute("SELECT * FROM categories ORDER BY id ASC").fetchall()
                return [self._category_row_to_dict(row) for row in rows]

    def update_category(self, category_id: int, category_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Kategoriyi günceller."""
        with self._lock:
            if not self.get_category_by_id(category_id):
                return None

            with self._get_connection() as conn:
                conn.execute(
                    """
                    UPDATE categories
                    SET name = ?, description = ?
                    WHERE id = ?
                    """,
                    (
                        category_data["name"],
                        category_data.get("description"),
                        category_id
                    )
                )
                conn.commit()

            return self.get_category_by_id(category_id)

    def delete_category(self, category_id: int) -> bool:
        """Kategoriyi siler."""
        with self._lock:
            if not self.get_category_by_id(category_id):
                return False

            with self._get_connection() as conn:
                conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
                conn.commit()
            return True

    # ==============================================================================
    # ÜRÜN (PRODUCT) VE ÇOKA-ÇOK KATEGORİ İŞLEMLERİ (MANY-TO-MANY)
    # ==============================================================================
    def _get_product_categories(self, conn: sqlite3.Connection, product_id: int) -> List[Dict[str, Any]]:
        """
        Belirli bir ürüne ait tüm kategorileri ara tablodan (product_categories) çeker.
        """
        rows = conn.execute(
            """
            SELECT c.id, c.name, c.description, c.created_at
            FROM categories c
            JOIN product_categories pc ON c.id = pc.category_id
            WHERE pc.product_id = ?
            ORDER BY c.id ASC
            """,
            (product_id,)
        ).fetchall()
        return [self._category_row_to_dict(row) for row in rows]

    def _product_row_to_dict(self, row: sqlite3.Row, categories_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ürün ve çoklu kategori listesini API yanıtı için tam sözlüğe dönüştürür.
        """
        cat_ids = [c["id"] for c in categories_list]
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "price": row["price"],
            "stock": row["stock"],
            "is_active": bool(row["is_active"]),
            "created_at": datetime.fromisoformat(row["created_at"]),
            "category_ids": cat_ids,
            "categories": categories_list
        }

    def add(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Yeni bir ürünü ve seçilen kategori ID'lerini (Many-to-Many) kaydeder.
        Verilen kategori ID'lerinden herhangi biri veritabanında yoksa ValueError fırlatır.
        """
        with self._lock:
            category_ids = product_data.get("category_ids", [])
            if not category_ids:
                raise ValueError("Ürün için en az bir geçerli kategori ID'si (category_ids) belirtilmelidir.")

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 1. Kategori ID'lerinin geçerliliğini doğrula (Foreign Key Denetimi)
                for cat_id in category_ids:
                    cat_row = cursor.execute("SELECT id FROM categories WHERE id = ?", (cat_id,)).fetchone()
                    if not cat_row:
                        raise ValueError(f"ID numarası '{cat_id}' olan kategori sistemde bulunamadı.")

                # 2. Ürünü products tablosuna ekle
                now = datetime.now(timezone.utc).isoformat()
                is_active_val = 1 if product_data.get("is_active", True) else 0

                cursor.execute(
                    """
                    INSERT INTO products (name, description, price, stock, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        product_data["name"],
                        product_data.get("description"),
                        product_data["price"],
                        product_data["stock"],
                        is_active_val,
                        now
                    )
                )
                product_id = cursor.lastrowid

                # 3. Kategori ilişkilerini product_categories tablosuna ekle
                for cat_id in set(category_ids):  # Mükerrer ID'leri engelle
                    cursor.execute(
                        """
                        INSERT INTO product_categories (product_id, category_id)
                        VALUES (?, ?)
                        """,
                        (product_id, cat_id)
                    )

                conn.commit()

            result = self.get_by_id(product_id)
            if not result:
                raise RuntimeError("Ürün kaydedildi ancak geri okunurken hata oluştu.")
            return result

    def get_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        ID numarasına göre ürünü kategorileriyle birlikte getirir.
        """
        with self._lock:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM products WHERE id = ?", (product_id,)
                ).fetchone()
                if not row:
                    return None

                categories = self._get_product_categories(conn, product_id)
                return self._product_row_to_dict(row, categories)

    def get_all(self) -> List[Dict[str, Any]]:
        """
        Tüm ürünleri ve dahil oldukları tüm kategorileri listeler.
        """
        with self._lock:
            with self._get_connection() as conn:
                rows = conn.execute("SELECT * FROM products ORDER BY id ASC").fetchall()
                products = []
                for row in rows:
                    categories = self._get_product_categories(conn, row["id"])
                    products.append(self._product_row_to_dict(row, categories))
                return products

    def update(self, product_id: int, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Mevcut bir ürünü ve kategori ilişkilerini baştan sona (PUT) günceller.
        """
        with self._lock:
            if not self.get_by_id(product_id):
                return None

            category_ids = product_data.get("category_ids", [])
            if not category_ids:
                raise ValueError("Ürün için en az bir kategori ID'si (category_ids) belirtilmelidir.")

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Kategori ID'lerini doğrula
                for cat_id in category_ids:
                    cat_row = cursor.execute("SELECT id FROM categories WHERE id = ?", (cat_id,)).fetchone()
                    if not cat_row:
                        raise ValueError(f"ID numarası '{cat_id}' olan kategori bulunamadı.")

                # Ürün bilgilerini güncelle
                is_active_val = 1 if product_data.get("is_active", True) else 0
                cursor.execute(
                    """
                    UPDATE products
                    SET name = ?, description = ?, price = ?, stock = ?, is_active = ?
                    WHERE id = ?
                    """,
                    (
                        product_data["name"],
                        product_data.get("description"),
                        product_data["price"],
                        product_data["stock"],
                        is_active_val,
                        product_id
                    )
                )

                # Eski kategori ilişkilerini temizle ve yenilerini ekle
                cursor.execute("DELETE FROM product_categories WHERE product_id = ?", (product_id,))
                for cat_id in set(category_ids):
                    cursor.execute(
                        "INSERT INTO product_categories (product_id, category_id) VALUES (?, ?)",
                        (product_id, cat_id)
                    )

                conn.commit()

            return self.get_by_id(product_id)

    def patch(self, product_id: int, partial_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Mevcut ürünü kısmi olarak (PATCH) günceller.
        """
        with self._lock:
            if not self.get_by_id(product_id):
                return None

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Eğer category_ids güncellenmek isteniyorsa
                if "category_ids" in partial_data and partial_data["category_ids"] is not None:
                    cat_ids = partial_data["category_ids"]
                    for cat_id in cat_ids:
                        cat_row = cursor.execute("SELECT id FROM categories WHERE id = ?", (cat_id,)).fetchone()
                        if not cat_row:
                            raise ValueError(f"ID numarası '{cat_id}' olan kategori bulunamadı.")

                    cursor.execute("DELETE FROM product_categories WHERE product_id = ?", (product_id,))
                    for cat_id in set(cat_ids):
                        cursor.execute(
                            "INSERT INTO product_categories (product_id, category_id) VALUES (?, ?)",
                            (product_id, cat_id)
                        )

                # Diğer alanları güncelle
                fields = []
                values = []
                for key in ["name", "description", "price", "stock", "is_active"]:
                    if key in partial_data and partial_data[key] is not None:
                        fields.append(f"{key} = ?")
                        val = partial_data[key]
                        if key == "is_active":
                            val = 1 if val else 0
                        values.append(val)

                if fields:
                    values.append(product_id)
                    query = f"UPDATE products SET {', '.join(fields)} WHERE id = ?"
                    cursor.execute(query, tuple(values))

                conn.commit()

            return self.get_by_id(product_id)

    def delete(self, product_id: int) -> bool:
        """
        Ürünü siler (Cascade kuralı ile kategori ilişkileri de silinir).
        """
        with self._lock:
            if not self.get_by_id(product_id):
                return False

            with self._get_connection() as conn:
                conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
                conn.commit()
            return True

    # ==============================================================================
    # SİPARİŞ (ORDER) VERİTABANI İŞLEMLERİ (ATOMİK & TRANSACTIONAL)
    # ==============================================================================
    def _order_row_to_dict(self, order_row: sqlite3.Row, item_rows: List[sqlite3.Row]) -> Dict[str, Any]:
        """
        Sipariş ve kalemlerini tam bir sözlük yapısına dönüştürür.
        """
        return {
            "id": order_row["id"],
            "customer_email": order_row["customer_email"],
            "total_amount": order_row["total_amount"],
            "status": order_row["status"],
            "created_at": datetime.fromisoformat(order_row["created_at"]),
            "items": [
                {
                    "id": item["id"],
                    "product_id": item["product_id"],
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"]
                }
                for item in item_rows
            ]
        }

    def create_order_atomic(self, customer_email: str, items_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Siparişi atomik olarak kaydeder, stokları düşer ve tutarı hesaplar.
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                total_amount = 0.0
                verified_items = []

                for item in items_data:
                    prod_id = item["product_id"]
                    req_qty = item["quantity"]

                    prod_row = cursor.execute(
                        "SELECT id, name, price, stock, is_active FROM products WHERE id = ?",
                        (prod_id,)
                    ).fetchone()

                    if not prod_row:
                        raise ValueError(f"ID'si '{prod_id}' olan ürün sistemde bulunamadı.")

                    if not prod_row["is_active"]:
                        raise ValueError(f"'{prod_row['name']}' adlı ürün satışta/aktif değildir.")

                    if prod_row["stock"] < req_qty:
                        raise ValueError(
                            f"Yetersiz stok: '{prod_row['name']}' için mevcut stok {prod_row['stock']}, istenen adet {req_qty}."
                        )

                    unit_price = prod_row["price"]
                    total_amount += unit_price * req_qty

                    verified_items.append({
                        "product_id": prod_id,
                        "quantity": req_qty,
                        "unit_price": unit_price
                    })

                now = datetime.now(timezone.utc).isoformat()
                cursor.execute(
                    """
                    INSERT INTO orders (customer_email, total_amount, status, created_at)
                    VALUES (?, ?, 'PENDING', ?)
                    """,
                    (customer_email, round(total_amount, 2), now)
                )
                order_id = cursor.lastrowid

                for v_item in verified_items:
                    cursor.execute(
                        """
                        INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                        VALUES (?, ?, ?, ?)
                        """,
                        (order_id, v_item["product_id"], v_item["quantity"], v_item["unit_price"])
                    )

                    cursor.execute(
                        """
                        UPDATE products
                        SET stock = stock - ?
                        WHERE id = ?
                        """,
                        (v_item["quantity"], v_item["product_id"])
                    )

                conn.commit()

            result = self.get_order_by_id(order_id)
            if not result:
                raise RuntimeError("Sipariş oluşturuldu ancak geri okunamadı.")
            return result

    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """
        ID'ye göre siparişi kalemleriyle birlikte getirir.
        """
        with self._lock:
            with self._get_connection() as conn:
                order_row = conn.execute(
                    "SELECT * FROM orders WHERE id = ?", (order_id,)
                ).fetchone()

                if not order_row:
                    return None

                item_rows = conn.execute(
                    "SELECT * FROM order_items WHERE order_id = ? ORDER BY id ASC", (order_id,)
                ).fetchall()

                return self._order_row_to_dict(order_row, item_rows)

    def get_all_orders(
        self,
        customer_email: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Tüm siparişleri filtre kriterleriyle listeler.
        """
        with self._lock:
            with self._get_connection() as conn:
                query = "SELECT * FROM orders WHERE 1=1"
                params = []

                if customer_email is not None:
                    query += " AND LOWER(customer_email) = LOWER(?)"
                    params.append(customer_email.strip())

                if status is not None:
                    query += " AND UPPER(status) = UPPER(?)"
                    params.append(status.strip())

                query += " ORDER BY id DESC"
                order_rows = conn.execute(query, tuple(params)).fetchall()

                orders_list = []
                for o_row in order_rows:
                    item_rows = conn.execute(
                        "SELECT * FROM order_items WHERE order_id = ? ORDER BY id ASC", (o_row["id"],)
                    ).fetchall()
                    orders_list.append(self._order_row_to_dict(o_row, item_rows))

                return orders_list

    def update_order_status_atomic(self, order_id: int, new_status: str) -> Optional[Dict[str, Any]]:
        """
        Sipariş durumunu atomik olarak günceller ve iptal halinde stoğu iade eder.
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                current_order = self.get_order_by_id(order_id)
                if not current_order:
                    return None

                current_status = current_order["status"].upper()
                target_status = new_status.upper()

                if current_status == target_status:
                    return current_order

                if current_status != "CANCELLED" and target_status == "CANCELLED":
                    for item in current_order["items"]:
                        cursor.execute(
                            "UPDATE products SET stock = stock + ? WHERE id = ?",
                            (item["quantity"], item["product_id"])
                        )

                elif current_status == "CANCELLED" and target_status != "CANCELLED":
                    for item in current_order["items"]:
                        prod_row = cursor.execute(
                            "SELECT stock, name FROM products WHERE id = ?",
                            (item["product_id"],)
                        ).fetchone()
                        if not prod_row or prod_row["stock"] < item["quantity"]:
                            raise ValueError(
                                f"Sipariş yeniden aktif edilemiyor: '{prod_row['name'] if prod_row else 'Ürün'}' için yetersiz stok."
                            )
                        cursor.execute(
                            "UPDATE products SET stock = stock - ? WHERE id = ?",
                            (item["quantity"], item["product_id"])
                        )

                cursor.execute(
                    "UPDATE orders SET status = ? WHERE id = ?",
                    (target_status, order_id)
                )
                conn.commit()

            return self.get_order_by_id(order_id)

    # ==============================================================================
    # TEMİZLEME VE BAŞLANGIÇ VERİSİ YÜKLEME
    # ==============================================================================
    def clear(self) -> None:
        """
        Tüm tablolardaki verileri temizler ve auto-increment sayaçlarını sıfırlar.
        """
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM product_categories")
                conn.execute("DELETE FROM order_items")
                conn.execute("DELETE FROM orders")
                conn.execute("DELETE FROM products")
                conn.execute("DELETE FROM categories")

                try:
                    conn.execute("DELETE FROM sqlite_sequence")
                except sqlite3.OperationalError:
                    pass
                conn.commit()

    def seed_initial_data(self) -> None:
        """
        Veritabanında eksik başlangıç kategorilerini ve örnek çoklu kategorili ürünleri yükler.
        """
        with self._lock:
            # 1. Eksik Olan Örnek Kategorileri Ekle
            sample_categories = [
                {"name": "Elektronik", "description": "Bilgisayar, monitör, klavye ve teknolojik ürünler."},
                {"name": "Mobilya", "description": "Ergonomik çalışma koltukları ve ofis masaları."},
                {"name": "Ev & Yaşam", "description": "Termos, matara ve günlük yaşam gereçleri."},
                {"name": "Aksesuar", "description": "Klavye tuş takımları, fare altlıkları ve aparatlar."},
                {"name": "Gaming", "description": "Oyuncu ekipmanları, RGB aydınlatmalı profesyonel donanımlar."},
            ]
            for cat in sample_categories:
                if not self.get_category_by_name(cat["name"]):
                    self.add_category(cat)

            # Güncel kategori isim -> ID haritasını çıkar
            all_cats = self.get_all_categories()
            cat_map = {c["name"]: c["id"] for c in all_cats}

            # 2. Ürünler Tablosu Boşsa Örnek Ürünleri Ekle
            with self._get_connection() as conn:
                prod_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
                if prod_count > 0:
                    return

            sample_products = [
                {
                    "name": "Kablosuz Mekanik Klavye",
                    "description": "RGB aydınlatmalı, Bluetooth & 2.4GHz bağlantılı mekanik klavye.",
                    "price": 1899.90,
                    "stock": 35,
                    "category_ids": [cat_map["Elektronik"], cat_map["Aksesuar"], cat_map["Gaming"]],
                    "is_active": True,
                },
                {
                    "name": "Ultra HD 4K Monitör 27 inç",
                    "description": "IPS panel, 144Hz yenileme hızı, HDR400 destekli profesyonel monitör.",
                    "price": 8450.00,
                    "stock": 12,
                    "category_ids": [cat_map["Elektronik"], cat_map["Gaming"]],
                    "is_active": True,
                },
                {
                    "name": "Ergonomik Ofis Koltuğu",
                    "description": "Bel desteği ayarlanabilir, nefes alabilen file kumaşlı çalışma koltuğu.",
                    "price": 4200.00,
                    "stock": 8,
                    "category_ids": [cat_map["Mobilya"], cat_map["Ev & Yaşam"]],
                    "is_active": True,
                },
                {
                    "name": "Paslanmaz Çelik Termos 750ml",
                    "description": "12 saat sıcak, 24 saat soğuk tutma kapasiteli çift cidarlı termos.",
                    "price": 650.00,
                    "stock": 50,
                    "category_ids": [cat_map["Ev & Yaşam"]],
                    "is_active": True,
                },
                {
                    "name": "Gürültü Engelleyici Kulaklık",
                    "description": "Aktif gürültü engelleme (ANC), 40 saat pil ömrü, Hi-Res ses sertifikalı.",
                    "price": 3150.00,
                    "stock": 0,
                    "category_ids": [cat_map["Elektronik"], cat_map["Aksesuar"]],
                    "is_active": False,
                },
            ]

            for item in sample_products:
                self.add(item)


# ==============================================================================
# VERİTABANI FABRİKASI (DATABASE FACTORY & DEPENDENCY INJECTION)
# ==============================================================================
_sqlite_instance: Optional[SQLiteDatabase] = None
_postgres_instance: Optional[IDatabase] = None


def get_database() -> IDatabase:
    """
    FastAPI Dependency Injection için veritabanı fabrika (Factory) fonksiyonu.
    DB_TYPE çevre değişkenine göre SQLite veya PostgreSQL adaptörünü döner:
    - DB_TYPE=sqlite (varsayılan): SQLiteDatabase örneğini döner.
    - DB_TYPE=postgres / postgresql: PostgresDatabase örneğini döner.
    """
    global _sqlite_instance, _postgres_instance
    db_type = os.getenv("DB_TYPE", "sqlite").strip().lower()

    if db_type in ("postgres", "postgresql"):
        if _postgres_instance is None:
            from adapters.postgres_database import PostgresDatabase
            _postgres_instance = PostgresDatabase()
        return _postgres_instance

    if _sqlite_instance is None:
        _sqlite_instance = SQLiteDatabase()
    return _sqlite_instance


class _DatabaseProxy:
    """
    Geriye dönük uyumluluk amacıyla db nesnesine yapılan çağrıları
    aktif veritabanı adaptörüne (SQLite veya Postgres) dinamik yönlendirir.
    """

    def __getattr__(self, name: str) -> Any:
        return getattr(get_database(), name)

    def __repr__(self) -> str:
        return f"<DatabaseProxy active_adapter={get_database().__class__.__name__}>"


# Global dinamik veritabanı nesnesi
db: IDatabase = _DatabaseProxy()  # type: ignore
