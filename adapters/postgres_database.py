"""
==============================================================================
PostgreSQL Veritabanı Adaptörü (PostgreSQL Database Adapter)
==============================================================================
Bu modül, Clean Architecture ve Adapter Pattern prensiplerine uygun olarak,
IDatabase ve Repository soyut arayüzlerini PostgreSQL veritabanı motoru
üzerinde implemente eder.

Temel Özellikler:
1. Thread-Safe Bağlantı ve Havuz Yönetimi (ThreadedConnectionPool)
2. Çevre Değişkenleri ile Dinamik Yapılandırma (.env veya OS Env)
3. PostgreSQL DDL Başlatma ve Şema Yönetimi (SERIAL, TIMESTAMPTZ, BOOLEAN)
4. Atomik Transaction Yönetimi (ACID)
==============================================================================
"""

import os
import sys
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import psycopg2
from psycopg2 import pool, extras
from interfaces.repositories import IDatabase


class PostgresDatabase(IDatabase):
    """
    IDatabase soyut arayüzünü (Interface) PostgreSQL veritabanı motoru
    üzerinde somutlaştıran (Concrete Adapter) thread-safe sınıf.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        connection_url: Optional[str] = None,
        min_connections: int = 1,
        max_connections: int = 10,
    ) -> None:
        """
        PostgreSQL bağlantı parametrelerini ve bağlantı havuzunu başlatır.
        Parametre verilmezse çevre değişkenlerinden (Environment Variables) okur.
        """
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.port = int(port or os.getenv("POSTGRES_PORT", "5432"))
        
        # Test ortamındaysa otomatik olarak test veritabanı adını kullan
        is_testing = "pytest" in sys.modules
        default_db = "test_proje_db" if is_testing else "proje_db"
        self.database = database or os.getenv("POSTGRES_DB", default_db)
        
        self.user = user or os.getenv("POSTGRES_USER", "postgres")
        self.password = password if password is not None else os.getenv("POSTGRES_PASSWORD", "")
        self.connection_url = connection_url or os.getenv("DATABASE_URL")

        self._lock = threading.RLock()
        self._pool: Optional[pool.ThreadedConnectionPool] = None
        self._min_conn = min_connections
        self._max_conn = max_connections

        # İlk başlatmada tabloları oluştur
        try:
            self.init_db()
        except Exception:
            # PostgreSQL sunucusu henüz ayakta değilse (örn. test ortamı mock'lanırken)
            # init_db çağrısı ertelenebilir veya mock'lanabilir.
            pass

    def _init_pool(self) -> pool.ThreadedConnectionPool:
        """
        Thread-safe PostgreSQL bağlantı havuzunu başlatır.
        """
        if self._pool is None:
            if self.connection_url:
                self._pool = pool.ThreadedConnectionPool(
                    self._min_conn,
                    self._max_conn,
                    dsn=self.connection_url,
                )
            else:
                self._pool = pool.ThreadedConnectionPool(
                    self._min_conn,
                    self._max_conn,
                    host=self.host,
                    port=self.port,
                    dbname=self.database,
                    user=self.user,
                    password=self.password,
                )
        return self._pool

    @contextmanager
    def _get_connection(self):
        """
        Bağlantı havuzundan güvenli bir PostgreSQL bağlantısı alır,
        işlem bitince havuza geri iade eder. Hata durumunda rollback uygular.
        """
        with self._lock:
            p = self._init_pool()
            conn = p.getconn()
            try:
                yield conn
            except Exception:
                conn.rollback()
                raise
            finally:
                p.putconn(conn)

    def init_db(self) -> None:
        """
        PostgreSQL veritabanı tablolarını ve kısıtlamalarını oluşturur.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Categories Tablosu
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS categories (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) UNIQUE NOT NULL,
                        description TEXT,
                        created_at TIMESTAMPTZ NOT NULL
                    );
                    """
                )

                # 2. Products Tablosu
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        price NUMERIC(10, 2) NOT NULL,
                        stock INT NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMPTZ NOT NULL
                    );
                    """
                )

                # 3. Product-Categories Çoka-Çok İlişki Tablosu (Many-to-Many Junction)
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS product_categories (
                        product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                        category_id INT NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
                        PRIMARY KEY (product_id, category_id)
                    );
                    """
                )

                # 4. Orders Tablosu
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS orders (
                        id SERIAL PRIMARY KEY,
                        customer_email VARCHAR(255) NOT NULL,
                        total_amount NUMERIC(10, 2) NOT NULL,
                        status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                        created_at TIMESTAMPTZ NOT NULL
                    );
                    """
                )

                # 5. Order Items Tablosu
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS order_items (
                        id SERIAL PRIMARY KEY,
                        order_id INT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                        product_id INT NOT NULL REFERENCES products(id),
                        quantity INT NOT NULL,
                        unit_price NUMERIC(10, 2) NOT NULL
                    );
                    """
                )
                conn.commit()

    def clear(self) -> None:
        """
        Tüm tablolardaki verileri güvenli ve ilişkisel sırayla temizler.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    TRUNCATE TABLE order_items, orders, product_categories, products, categories
                    RESTART IDENTITY CASCADE;
                    """
                )
                conn.commit()

    # ==============================================================================
    # YARDIMCI DÖNÜŞTÜRÜCÜ METOTLAR (ROW TO DICT MAPPERS)
    # ==============================================================================
    def _category_row_to_dict(self, row: Any) -> Dict[str, Any]:
        """Kategori satırını şema uyumlu sözlüğe dönüştürür."""
        created_at = row["created_at"]
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "created_at": created_at,
        }

    def _product_row_to_dict(self, row: Any, categories: Any) -> Dict[str, Any]:
        """Ürün satırını ve kategorilerini şema uyumlu sözlüğe dönüştürür."""
        created_at = row["created_at"]
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "price": float(row["price"]),
            "stock": int(row["stock"]),
            "is_active": bool(row["is_active"]),
            "created_at": created_at,
            "category_ids": [c["id"] for c in categories],
            "categories": list(categories),
        }

    def _order_row_to_dict(self, order_row: Any, items: Any) -> Dict[str, Any]:
        """Sipariş satırını ve kalemlerini şema uyumlu sözlüğe dönüştürür."""
        created_at = order_row["created_at"]
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        return {
            "id": order_row["id"],
            "customer_email": order_row["customer_email"],
            "total_amount": float(order_row["total_amount"]),
            "status": order_row["status"],
            "created_at": created_at,
            "items": [
                {
                    "id": item["id"],
                    "product_id": item["product_id"],
                    "quantity": int(item["quantity"]),
                    "unit_price": float(item["unit_price"]),
                }
                for item in items
            ],
        }

    # ==============================================================================
    # KATEGORİ (CATEGORY) VERİ ERİŞİM OPERASYONLARI (ICategoryRepository)
    # ==============================================================================
    def add_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Yeni bir kategori kaydeder."""
        now = datetime.now(timezone.utc)
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO categories (name, description, created_at)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        category_data["name"],
                        category_data.get("description"),
                        now,
                    ),
                )
                created_row = cursor.fetchone()
                if not created_row:
                    raise RuntimeError("Kategori oluşturulamadı.")
                new_id = created_row["id"]
                conn.commit()

        result = self.get_category_by_id(new_id)
        if not result:
            raise RuntimeError("Kategori kaydedildi ancak geri okunurken hata oluştu.")
        return result

    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """ID'ye göre kategori getirir."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM categories WHERE id = %s;", (category_id,))
                row = cursor.fetchone()
                if row:
                    return self._category_row_to_dict(row)
                return None

    def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """İsme göre kategori getirir (Büyük/küçük harf duyarsız)."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM categories WHERE LOWER(name) = LOWER(%s);",
                    (name.strip(),),
                )
                row = cursor.fetchone()
                if row:
                    return self._category_row_to_dict(row)
                return None

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Tüm kategorileri listeler."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM categories ORDER BY id ASC;")
                rows = cursor.fetchall()
                return [self._category_row_to_dict(row) for row in rows]

    def update_category(self, category_id: int, category_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Kategoriyi günceller."""
        if not self.get_category_by_id(category_id):
            return None

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE categories
                    SET name = %s, description = %s
                    WHERE id = %s;
                    """,
                    (
                        category_data["name"],
                        category_data.get("description"),
                        category_id,
                    ),
                )
                conn.commit()

        return self.get_category_by_id(category_id)

    def delete_category(self, category_id: int) -> bool:
        """Kategoriyi siler."""
        if not self.get_category_by_id(category_id):
            return False

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM categories WHERE id = %s;", (category_id,))
                conn.commit()
            return True

    # ==============================================================================
    # ÜRÜN (PRODUCT) VE ÇOKA-ÇOK KATEGORİ OPERASYONLARI (IProductRepository)
    # ==============================================================================
    def _get_product_categories(self, cursor, product_id: int) -> List[Dict[str, Any]]:
        """Ürüne ait kategorileri ara tablodan çeker."""
        cursor.execute(
            """
            SELECT c.id, c.name, c.description, c.created_at
            FROM categories c
            JOIN product_categories pc ON c.id = pc.category_id
            WHERE pc.product_id = %s
            ORDER BY c.id ASC;
            """,
            (product_id,),
        )
        rows = cursor.fetchall()
        return [self._category_row_to_dict(row) for row in rows]

    def add(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Yeni bir ürün ve kategori ilişkilerini (Many-to-Many) kaydeder."""
        category_ids = product_data.get("category_ids", [])
        if not category_ids:
            raise ValueError("Ürün için en az bir geçerli kategori ID'si (category_ids) belirtilmelidir.")

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                # 1. Kategori ID'lerinin geçerliliğini doğrula
                for cat_id in category_ids:
                    cursor.execute("SELECT id FROM categories WHERE id = %s;", (cat_id,))
                    if not cursor.fetchone():
                        raise ValueError(f"ID numarası '{cat_id}' olan kategori sistemde bulunamadı.")

                # 2. Ürünü products tablosuna ekle
                now = datetime.now(timezone.utc)
                cursor.execute(
                    """
                    INSERT INTO products (name, description, price, stock, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        product_data["name"],
                        product_data.get("description"),
                        product_data["price"],
                        product_data["stock"],
                        product_data.get("is_active", True),
                        now,
                    ),
                )
                created_row = cursor.fetchone()
                if not created_row:
                    raise RuntimeError("Ürün oluşturulamadı.")
                product_id = created_row["id"]

                # 3. Kategori ilişkilerini ara tabloya ekle
                for cat_id in set(category_ids):
                    cursor.execute(
                        """
                        INSERT INTO product_categories (product_id, category_id)
                        VALUES (%s, %s);
                        """,
                        (product_id, cat_id),
                    )

                conn.commit()

        result = self.get_by_id(product_id)
        if not result:
            raise RuntimeError("Ürün kaydedildi ancak geri okunurken hata oluştu.")
        return result

    def get_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """ID numarasına göre ürünü kategorileriyle birlikte getirir."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM products WHERE id = %s;", (product_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                categories = self._get_product_categories(cursor, product_id)
                return self._product_row_to_dict(row, categories)

    def get_all(self) -> List[Dict[str, Any]]:
        """Tüm ürünleri ve kategorilerini listeler."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM products ORDER BY id ASC;")
                rows = cursor.fetchall()
                products = []
                for row in rows:
                    categories = self._get_product_categories(cursor, row["id"])
                    products.append(self._product_row_to_dict(row, categories))
                return products

    def update(self, product_id: int, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mevcut bir ürünü ve kategori ilişkilerini baştan sona (PUT) günceller."""
        if not self.get_by_id(product_id):
            return None

        category_ids = product_data.get("category_ids", [])
        if not category_ids:
            raise ValueError("Ürün için en az bir kategori ID'si (category_ids) belirtilmelidir.")

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                for cat_id in category_ids:
                    cursor.execute("SELECT id FROM categories WHERE id = %s;", (cat_id,))
                    if not cursor.fetchone():
                        raise ValueError(f"ID numarası '{cat_id}' olan kategori bulunamadı.")

                cursor.execute(
                    """
                    UPDATE products
                    SET name = %s, description = %s, price = %s, stock = %s, is_active = %s
                    WHERE id = %s;
                    """,
                    (
                        product_data["name"],
                        product_data.get("description"),
                        product_data["price"],
                        product_data["stock"],
                        product_data.get("is_active", True),
                        product_id,
                    ),
                )

                cursor.execute("DELETE FROM product_categories WHERE product_id = %s;", (product_id,))
                for cat_id in set(category_ids):
                    cursor.execute(
                        "INSERT INTO product_categories (product_id, category_id) VALUES (%s, %s);",
                        (product_id, cat_id),
                    )

                conn.commit()

        return self.get_by_id(product_id)

    def patch(self, product_id: int, partial_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mevcut ürünü kısmi olarak (PATCH) günceller."""
        if not self.get_by_id(product_id):
            return None

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                if "category_ids" in partial_data and partial_data["category_ids"] is not None:
                    cat_ids = partial_data["category_ids"]
                    for cat_id in cat_ids:
                        cursor.execute("SELECT id FROM categories WHERE id = %s;", (cat_id,))
                        if not cursor.fetchone():
                            raise ValueError(f"ID numarası '{cat_id}' olan kategori bulunamadı.")

                    cursor.execute("DELETE FROM product_categories WHERE product_id = %s;", (product_id,))
                    for cat_id in set(cat_ids):
                        cursor.execute(
                            "INSERT INTO product_categories (product_id, category_id) VALUES (%s, %s);",
                            (product_id, cat_id),
                        )

                fields = []
                values = []
                for key in ["name", "description", "price", "stock", "is_active"]:
                    if key in partial_data and partial_data[key] is not None:
                        fields.append(f"{key} = %s")
                        values.append(partial_data[key])

                if fields:
                    values.append(product_id)
                    query = f"UPDATE products SET {', '.join(fields)} WHERE id = %s;"
                    cursor.execute(query, tuple(values))

                conn.commit()

        return self.get_by_id(product_id)

    def delete(self, product_id: int) -> bool:
        """Ürünü siler."""
        if not self.get_by_id(product_id):
            return False

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM products WHERE id = %s;", (product_id,))
                conn.commit()
            return True

    # ==============================================================================
    # SİPARİŞ (ORDER) VERİ ERİŞİM OPERASYONLARI (IOrderRepository)
    # ==============================================================================
    def create_order_atomic(self, customer_email: str, items_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Siparişi atomik olarak kaydeder, stokları düşer ve tutarı hesaplar."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                total_amount = 0.0
                verified_items = []

                for item in items_data:
                    prod_id = item["product_id"]
                    req_qty = item["quantity"]

                    cursor.execute(
                        "SELECT id, name, price, stock, is_active FROM products WHERE id = %s FOR UPDATE;",
                        (prod_id,),
                    )
                    prod_row = cursor.fetchone()

                    if not prod_row:
                        raise ValueError(f"ID'si '{prod_id}' olan ürün sistemde bulunamadı.")

                    if not prod_row["is_active"]:
                        raise ValueError(f"'{prod_row['name']}' adlı ürün satışta/aktif değildir.")

                    if prod_row["stock"] < req_qty:
                        raise ValueError(
                            f"Yetersiz stok: '{prod_row['name']}' için mevcut stok {prod_row['stock']}, istenen adet {req_qty}."
                        )

                    unit_price = float(prod_row["price"])
                    total_amount += unit_price * req_qty

                    verified_items.append({
                        "product_id": prod_id,
                        "quantity": req_qty,
                        "unit_price": unit_price,
                    })

                now = datetime.now(timezone.utc)
                cursor.execute(
                    """
                    INSERT INTO orders (customer_email, total_amount, status, created_at)
                    VALUES (%s, %s, 'PENDING', %s)
                    RETURNING id;
                    """,
                    (customer_email, round(total_amount, 2), now),
                )
                created_row = cursor.fetchone()
                if not created_row:
                    raise RuntimeError("Sipariş oluşturulamadı.")
                order_id = created_row["id"]

                for v_item in verified_items:
                    cursor.execute(
                        """
                        INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                        VALUES (%s, %s, %s, %s);
                        """,
                        (order_id, v_item["product_id"], v_item["quantity"], v_item["unit_price"]),
                    )

                    cursor.execute(
                        """
                        UPDATE products
                        SET stock = stock - %s
                        WHERE id = %s;
                        """,
                        (v_item["quantity"], v_item["product_id"]),
                    )

                conn.commit()

        result = self.get_order_by_id(order_id)
        if not result:
            raise RuntimeError("Sipariş oluşturuldu ancak geri okunamadı.")
        return result

    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """ID'ye göre siparişi kalemleriyle birlikte getirir."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM orders WHERE id = %s;", (order_id,))
                order_row = cursor.fetchone()
                if not order_row:
                    return None

                cursor.execute("SELECT * FROM order_items WHERE order_id = %s ORDER BY id ASC;", (order_id,))
                items = cursor.fetchall()
                return self._order_row_to_dict(order_row, items)

    def get_all_orders(
        self,
        customer_email: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Tüm siparişleri filtre kriterleriyle listeler."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                query = "SELECT * FROM orders WHERE 1=1"
                params = []

                if customer_email is not None:
                    query += " AND LOWER(customer_email) = LOWER(%s)"
                    params.append(customer_email.strip())

                if status is not None:
                    query += " AND UPPER(status) = UPPER(%s)"
                    params.append(status.strip())

                query += " ORDER BY id DESC;"
                cursor.execute(query, tuple(params))
                order_rows = cursor.fetchall()

                orders_list = []
                for o_row in order_rows:
                    cursor.execute("SELECT * FROM order_items WHERE order_id = %s ORDER BY id ASC;", (o_row["id"],))
                    items = cursor.fetchall()
                    orders_list.append(self._order_row_to_dict(o_row, items))

                return orders_list

    def update_order_status_atomic(self, order_id: int, new_status: str) -> Optional[Dict[str, Any]]:
        """Sipariş durumunu atomik günceller ve iptal halinde stoğu iade eder."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                current_order = self.get_order_by_id(order_id)
                if not current_order:
                    return None

                current_status = current_order["status"].upper()
                target_status = new_status.upper()

                if current_status == target_status:
                    return current_order

                # İptal edilirse stoğu iade et
                if current_status != "CANCELLED" and target_status == "CANCELLED":
                    for item in current_order["items"]:
                        cursor.execute(
                            "UPDATE products SET stock = stock + %s WHERE id = %s;",
                            (item["quantity"], item["product_id"]),
                        )

                # İptalden başka duruma çekilirse tekrar stok düş
                elif current_status == "CANCELLED" and target_status != "CANCELLED":
                    for item in current_order["items"]:
                        cursor.execute(
                            "SELECT stock, name FROM products WHERE id = %s FOR UPDATE;",
                            (item["product_id"],),
                        )
                        prod_row = cursor.fetchone()
                        if not prod_row or prod_row["stock"] < item["quantity"]:
                            current_stk = prod_row["stock"] if prod_row else 0
                            raise ValueError(
                                f"Stok yetersizliği nedeniyle sipariş iptalden çıkartılamıyor: "
                                f"'{prod_row['name'] if prod_row else 'Ürün'}' için mevcut stok {current_stk}, "
                                f"gerekli adet {item['quantity']}."
                            )
                        cursor.execute(
                            "UPDATE products SET stock = stock - %s WHERE id = %s;",
                            (item["quantity"], item["product_id"]),
                        )

                cursor.execute(
                    "UPDATE orders SET status = %s WHERE id = %s;",
                    (target_status, order_id),
                )
                conn.commit()

        return self.get_order_by_id(order_id)

    def seed_initial_data(self) -> None:
        """PostgreSQL veritabanında başlangıç kategorilerini ve örnek ürünleri yükler."""
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
            if len(self.get_all()) > 0:
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
