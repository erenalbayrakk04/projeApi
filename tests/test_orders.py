"""
==============================================================================
Sipariş Modülü Otomatik Test Paketi (Pytest & TestClient)
==============================================================================
Bu dosya, Sipariş (Order) domaini için:
- Sipariş oluşturma ve toplam tutar hesaplama doğruluğu,
- Otomatik stok düşümü ve yetersiz stok senaryosu,
- Geçersiz ürün ve e-posta validasyonları,
- Sipariş listeleme ve durum güncellemeleri,
- Sipariş iptalinde (CANCELLED) stok iade mekanizmasını
test eder.
==============================================================================
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from database import db


@pytest.fixture(autouse=True)
def reset_database():
    """
    Her test öncesi veritabanını sıfırlar ve test verilerini yükler.
    """
    db.clear()
    db.seed_initial_data()
    yield
    db.clear()


client = TestClient(app)


def test_create_order_success_and_stock_deduction():
    """
    Başarılı sipariş oluşturma, doğru toplam tutar hesabı ve ürün stok düşümünü test eder.
    """
    # 1. Başlangıçta ürün 1'in stoğunu öğren (Seed datada: Klavye fiyat 1899.90, stok 35)
    prod_res_before = client.get("/products/1")
    assert prod_res_before.status_code == 200
    initial_stock = prod_res_before.json()["stock"]
    unit_price = prod_res_before.json()["price"]

    # 2. 2 adet sipariş ver
    order_payload = {
        "customer_email": "eren.albayrak@example.com",
        "items": [
            {
                "product_id": 1,
                "quantity": 2
            }
        ]
    }
    response = client.post("/orders/", json=order_payload)
    assert response.status_code == 201

    order_data = response.json()
    assert order_data["customer_email"] == order_payload["customer_email"]
    assert order_data["status"] == "PENDING"
    assert len(order_data["items"]) == 1
    assert order_data["items"][0]["quantity"] == 2
    assert order_data["items"][0]["unit_price"] == unit_price
    # Toplam tutar: 2 * 1899.90 = 3799.80 olmalı
    assert order_data["total_amount"] == round(unit_price * 2, 2)

    # 3. Ürün stoğunun 35 - 2 = 33'e düştüğünü doğrula
    prod_res_after = client.get("/products/1")
    assert prod_res_after.json()["stock"] == initial_stock - 2


def test_create_order_insufficient_stock():
    """
    Mevcut stoktan fazla adet sipariş edilmek istendiğinde 400 Bad Request döndüğünü
    ve stoğun kesinlikle değişmediğini test eder.
    """
    prod_res = client.get("/products/1")
    stock = prod_res.json()["stock"]  # 35

    order_payload = {
        "customer_email": "eren@example.com",
        "items": [
            {
                "product_id": 1,
                "quantity": stock + 100  # Yetersiz stok
            }
        ]
    }
    response = client.post("/orders/", json=order_payload)
    assert response.status_code == 400
    assert "Yetersiz stok" in response.json()["detail"]

    # Stoğun değişmediğini doğrula
    prod_after = client.get("/products/1")
    assert prod_after.json()["stock"] == stock


def test_create_order_nonexistent_product():
    """
    Sistemde bulunmayan bir ürün ID'si sipariş edildiğinde 404 hatası döndüğünü test eder.
    """
    order_payload = {
        "customer_email": "eren@example.com",
        "items": [
            {
                "product_id": 99999,
                "quantity": 1
            }
        ]
    }
    response = client.post("/orders/", json=order_payload)
    assert response.status_code == 404
    assert "bulunamadı" in response.json()["detail"]


def test_create_order_inactive_product():
    """
    Satışta olmayan (is_active=False) bir ürün sipariş edildiğinde 400 döndüğünü test eder.
    """
    # Seed datada kulaklık (ID: 5) pasif üründür (is_active=False)
    order_payload = {
        "customer_email": "eren@example.com",
        "items": [
            {"product_id": 5, "quantity": 1}
        ]
    }
    response = client.post("/orders/", json=order_payload)
    assert response.status_code == 400
    assert "aktif değildir" in response.json()["detail"]


def test_create_order_invalid_email_and_empty_items():
    """
    Geçersiz e-posta adresi veya boş ürün listesinde Pydantic 422 hatası döndüğünü test eder.
    """
    # Geçersiz email
    res1 = client.post("/orders/", json={"customer_email": "invalid-email", "items": [{"product_id": 1, "quantity": 1}]})
    assert res1.status_code == 422

    # Boş ürün listesi
    res2 = client.post("/orders/", json={"customer_email": "eren@example.com", "items": []})
    assert res2.status_code == 422


def test_get_order_by_id_success_and_not_found():
    """
    ID ile sipariş sorgulama ve 404 senaryolarını test eder.
    """
    # 1. Sipariş oluştur
    create_res = client.post("/orders/", json={
        "customer_email": "eren@example.com",
        "items": [{"product_id": 1, "quantity": 1}]
    })
    order_id = create_res.json()["id"]

    # 2. Getir
    get_res = client.get(f"/orders/{order_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == order_id

    # 3. Olmayan sipariş
    not_found_res = client.get("/orders/99999")
    assert not_found_res.status_code == 404


def test_list_and_filter_orders():
    """
    Siparişleri listeleme ve filtreleme (e-posta & durum) test edilir.
    """
    # 2 sipariş oluştur
    client.post("/orders/", json={"customer_email": "musteri1@example.com", "items": [{"product_id": 1, "quantity": 1}]})
    client.post("/orders/", json={"customer_email": "musteri2@example.com", "items": [{"product_id": 2, "quantity": 1}]})

    # Toplam liste
    res_all = client.get("/orders/")
    assert res_all.status_code == 200
    assert len(res_all.json()) == 2

    # E-postaya göre filtrele
    res_email = client.get("/orders/?customer_email=musteri1@example.com")
    assert res_email.status_code == 200
    assert len(res_email.json()) == 1
    assert res_email.json()[0]["customer_email"] == "musteri1@example.com"


def test_order_cancellation_restores_stock():
    """
    Sipariş CANCELLED (İptal) durumuna getirildiğinde düşülen stokların
    otomatik olarak geri iade edildiğini doğrular.
    """
    # 1. Başlangıç stok: 35
    prod_before = client.get("/products/1").json()
    stock_initial = prod_before["stock"]

    # 2. 5 adet sipariş oluştur -> Stok 30'a düşmeli
    order_res = client.post("/orders/", json={
        "customer_email": "eren@example.com",
        "items": [{"product_id": 1, "quantity": 5}]
    })
    order_id = order_res.json()["id"]
    assert client.get("/products/1").json()["stock"] == stock_initial - 5

    # 3. Siparişi CANCELLED yap
    patch_res = client.patch(f"/orders/{order_id}/status", json={"status": "CANCELLED"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "CANCELLED"

    # 4. Stoğun tekrar eski haline (35) geri iade edildiğini doğrula!
    prod_after_cancel = client.get("/products/1").json()
    assert prod_after_cancel["stock"] == stock_initial
