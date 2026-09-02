"""
==============================================================================
Otomatik Test Paketi (Pytest & FastAPI TestClient) - Ürün Modülü
==============================================================================
Bu dosya, Product API'nin tüm CRUD endpoint'lerini, Pydantic validasyon kurallarını,
fiyat/kategori filtrelerini, çoklu kategori ID (Many-to-Many) yönetimini, sayfalama
mekanizmasını ve eşzamanlı (Thread-Safe) çalışma güvenilirliğini test eder.
==============================================================================
"""

from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient

from main import app
from database import db


@pytest.fixture(autouse=True)
def reset_database():
    """
    Her test öncesinde ve sonrasında veritabanını temizler ve test seed verilerini yükler.
    """
    db.clear()
    db.seed_initial_data()
    yield
    db.clear()


client = TestClient(app)


# ==============================================================================
# 1. Kök ve Sağlık Kontrolü Testleri
# ==============================================================================
def test_root_endpoint():
    """
    GET / isteğinin 200 OK döndüğünü ve beklenen sistem anahtarlarını içerdiğini doğrular.
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["version"] == "1.0.0"
    assert "/docs" in data["documentation"]["swagger_ui"]


def test_health_check_endpoint():
    """
    GET /health isteğinin 200 OK döndüğünü ve başlangıç seed sayılarını doğruladığını test eder.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["total_active_records"] == 5


# ==============================================================================
# 2. Yeni Ürün Ekleme (POST) ve Validasyon Testleri
# ==============================================================================
def test_create_product_success():
    """
    Geçerli bir ürün ve category_ids verisiyle POST /products/ çağrıldığında
    201 Created döndüğünü, otomatik 'id' ve 'created_at' oluşturulduğunu doğrular.
    """
    payload = {
        "name": "Kablosuz Kulaklık Pro",
        "description": "Yüksek kaliteli ses ve aktif gürültü engelleme.",
        "price": 2499.99,
        "stock": 50,
        "category_ids": [1, 4],  # Elektronik ve Aksesuar
        "is_active": True,
    }

    response = client.post("/products/", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == payload["name"]
    assert data["price"] == payload["price"]
    assert data["stock"] == payload["stock"]
    assert data["category_ids"] == [1, 4]
    assert len(data["categories"]) == 2
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert isinstance(data["id"], int)


def test_create_product_nonexistent_category():
    """
    Var olmayan bir category_id ile ürün eklenmek istendiğinde 404 döndüğünü test eder.
    """
    payload = {
        "name": "Geçersiz Kategorili Ürün",
        "price": 999.0,
        "stock": 10,
        "category_ids": [99999],  # Sistemde yok
    }
    response = client.post("/products/", json=payload)
    assert response.status_code == 404
    assert "bulunamadı" in response.json()["detail"]


@pytest.mark.parametrize(
    "invalid_payload, expected_error_loc",
    [
        # 1. Hata: İsim 2 karakterden kısa ("A")
        (
            {"name": "A", "price": 100, "stock": 5, "category_ids": [1]},
            "name",
        ),
        # 2. Hata: Fiyat negatif (-10)
        (
            {"name": "Geçerli İsim", "price": -10, "stock": 5, "category_ids": [1]},
            "price",
        ),
        # 3. Hata: Fiyat sıfır (0)
        (
            {"name": "Geçerli İsim", "price": 0, "stock": 5, "category_ids": [1]},
            "price",
        ),
        # 4. Hata: Stok negatif (-1)
        (
            {"name": "Geçerli İsim", "price": 100, "stock": -1, "category_ids": [1]},
            "stock",
        ),
        # 5. Hata: Zorunlu olan 'name' alanı gönderilmemiş
        (
            {"price": 100, "stock": 5, "category_ids": [1]},
            "name",
        ),
        # 6. Hata: category_ids boş liste veya gönderilmemiş
        (
            {"name": "Geçerli İsim", "price": 100, "stock": 5, "category_ids": []},
            "category_ids",
        ),
    ],
)
def test_create_product_validation_errors(invalid_payload, expected_error_loc):
    """
    Pydantic v2 kural ihlallerinde 422 Unprocessable Entity döndüğünü test eder.
    """
    response = client.post("/products/", json=invalid_payload)
    assert response.status_code == 422

    errors = response.json().get("detail", [])
    locs = [err["loc"][-1] for err in errors]
    assert expected_error_loc in locs


# ==============================================================================
# 3. Ürünleri Listeleme, Filtreleme ve Sayfalama Testleri (GET)
# ==============================================================================
def test_get_all_products_and_pagination():
    """
    Sayfalama (skip ve limit) parametrelerinin doğru dilimleme yaptığını test eder.
    """
    response = client.get("/products/")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 5

    page_1 = client.get("/products/?skip=0&limit=2")
    assert page_1.status_code == 200
    p1_data = page_1.json()
    assert len(p1_data) == 2

    page_2 = client.get("/products/?skip=2&limit=2")
    assert page_2.status_code == 200
    p2_data = page_2.json()
    assert len(p2_data) == 2

    assert p1_data[0]["id"] != p2_data[0]["id"]


def test_filter_products_by_category_name():
    """
    Kategori adına göre filtrelemenin (büyük/küçük harf duyarsız) çalıştığını test eder.
    """
    response = client.get("/products/?category=Elektronik")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 3  # Klavye, Monitör, Kulaklık
    for p in products:
        assert any(c["name"].lower() == "elektronik" for c in p["categories"])


def test_filter_products_by_category_id():
    """
    Kategori ID'sine göre filtrelemenin çalıştığını test eder.
    """
    # Kategori ID: 5 (Gaming) olan ürünleri sorgula (Klavye ve Monitör)
    response = client.get("/products/?category_id=5")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 2
    for p in products:
        assert 5 in p["category_ids"]


def test_filter_products_by_price_range():
    """
    Fiyat aralığı (min_price ve max_price) filtrelemesini test eder.
    """
    response = client.get("/products/?min_price=1000&max_price=4500")
    assert response.status_code == 200
    products = response.json()
    for p in products:
        assert 1000 <= p["price"] <= 4500


def test_invalid_price_range():
    """
    min_price > max_price olduğunda API'nin 400 Bad Request döndüğünü test eder.
    """
    response = client.get("/products/?min_price=5000&max_price=1000")
    assert response.status_code == 400
    assert "min_price" in response.json()["detail"]


def test_filter_products_by_is_active():
    """
    is_active=false filtresinin sadece pasif ürünleri getirdiğini test eder.
    """
    response = client.get("/products/?is_active=false")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 1
    assert products[0]["is_active"] is False


# ==============================================================================
# 4. ID ile Tekil Ürün Getirme Testleri (GET /products/{id})
# ==============================================================================
def test_get_product_by_id_success():
    """Mevcut bir ürün ID'si (1) sorgulandığında 200 OK döndüğünü test eder."""
    response = client.get("/products/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Kablosuz Mekanik Klavye"
    assert len(data["categories"]) >= 1


def test_get_product_by_id_not_found():
    """Olmayan bir ID (99999) sorgulandığında 404 Not Found döndüğünü test eder."""
    response = client.get("/products/99999")
    assert response.status_code == 404


# ==============================================================================
# 5. Tam Güncelleme Testleri (PUT /products/{id})
# ==============================================================================
def test_update_product_put_success():
    """Mevcut bir ürünün PUT ile başarıyla güncellendiğini ve 200 döndüğünü test eder."""
    update_payload = {
        "name": "Yenilenmiş Mekanik Klavye V2",
        "description": "Tamamen yenilenmiş Türkçe Q tuş dizilimli model.",
        "price": 2200.00,
        "stock": 15,
        "category_ids": [1, 5],
        "is_active": True,
    }
    response = client.put("/products/1", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == update_payload["name"]
    assert data["price"] == update_payload["price"]
    assert data["stock"] == update_payload["stock"]
    assert data["category_ids"] == [1, 5]


def test_update_product_put_not_found():
    """Olmayan ürün güncellenmek istendiğinde 404 döndüğünü test eder."""
    update_payload = {
        "name": "Hayali Ürün",
        "description": "Açıklama",
        "price": 500.0,
        "stock": 10,
        "category_ids": [1],
        "is_active": True,
    }
    response = client.put("/products/99999", json=update_payload)
    assert response.status_code == 404


# ==============================================================================
# 6. Kısmi Güncelleme Testleri (PATCH /products/{id})
# ==============================================================================
def test_patch_product_success():
    """
    Sadece fiyat ve stok alanları gönderildiğinde diğer alanların korunduğunu test eder.
    """
    patch_payload = {
        "price": 1750.50,
        "stock": 100,
    }
    response = client.patch("/products/1", json=patch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["price"] == 1750.50
    assert data["stock"] == 100
    assert data["name"] == "Kablosuz Mekanik Klavye"
    assert 1 in data["category_ids"]


def test_patch_product_not_found():
    """Olmayan bir ürüne PATCH isteği yapıldığında 404 döndüğünü test eder."""
    patch_payload = {"price": 100.0}
    response = client.patch("/products/99999", json=patch_payload)
    assert response.status_code == 404


# ==============================================================================
# 7. Ürün Silme Testleri (DELETE /products/{id})
# ==============================================================================
def test_delete_product_success():
    """
    Ürün silindiğinde 204 No Content döndüğünü ve ardından arandığında 404 döndüğünü test eder.
    """
    delete_response = client.delete("/products/1")
    assert delete_response.status_code == 204

    get_response = client.get("/products/1")
    assert get_response.status_code == 404


def test_delete_product_not_found():
    """Olmayan ürünü silmeye çalışırken 404 döndüğünü test eder."""
    response = client.delete("/products/99999")
    assert response.status_code == 404


# ==============================================================================
# 8. Thread-Safety Testi
# ==============================================================================
def test_thread_safety_concurrent_creates():
    """
    Çoklu iş parçacıklı isteklerde veritabanı kilit güvenliğini test eder.
    """
    total_threads = 50

    def create_single_product(index: int):
        return client.post(
            "/products/",
            json={
                "name": f"Eşzamanlı Ürün {index}",
                "description": "Thread-safety concurrency testi",
                "price": 100.0 + index,
                "stock": index,
                "category_ids": [1],
                "is_active": True,
            },
        )

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(create_single_product, range(total_threads)))

    for r in results:
        assert r.status_code == 201

    all_products_response = client.get("/products/?limit=100")
    products = all_products_response.json()
    assert len(products) == 55

    ids = [p["id"] for p in products]
    assert len(ids) == len(set(ids))
