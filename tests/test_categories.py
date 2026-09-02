"""
==============================================================================
Kategori Modülü Otomatik Test Paketi (Pytest & TestClient)
==============================================================================
Bu dosya, Kategori (Category) domaini için tüm CRUD operasyonlarını,
isim benzersizliği kurallarını ve sayfalama parametrelerini test eder.
==============================================================================
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from database import db


@pytest.fixture(autouse=True)
def reset_database():
    """
    Her test fonksiyonu öncesinde veritabanını temizler ve test verilerini yükler.
    """
    db.clear()
    db.seed_initial_data()
    yield
    db.clear()


client = TestClient(app)


def test_create_category_success():
    """Yeni kategori oluşturma (POST /categories/) test edilir."""
    payload = {
        "name": "Kitap & Kırtasiye",
        "description": "Romanlar, ders kitapları ve ofis gereçleri."
    }
    response = client.post("/categories/", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert "id" in data
    assert "created_at" in data


def test_create_category_duplicate_name():
    """Aynı isimde kategori eklendiğinde 409 Conflict döndüğü test edilir."""
    payload = {
        "name": "Elektronik",  # Seed datada zaten var
        "description": "Mükerrer kategori açıklaması."
    }
    response = client.post("/categories/", json=payload)
    assert response.status_code == 409
    assert "zaten mevcut" in response.json()["detail"]


def test_create_category_validation_error():
    """Kategori adı 2 karakterden kısa olduğunda 422 döndüğü test edilir."""
    payload = {"name": "A"}
    response = client.post("/categories/", json=payload)
    assert response.status_code == 422


def test_list_categories_and_pagination():
    """Kategorilerin listelenmesi ve sayfalama (skip/limit) test edilir."""
    # Varsayılan sorgu (Seed datadaki 5 kategori gelmeli)
    response = client.get("/categories/")
    assert response.status_code == 200
    cats = response.json()
    assert len(cats) == 5

    # Sayfalama: skip=0, limit=2
    page1 = client.get("/categories/?skip=0&limit=2")
    assert page1.status_code == 200
    assert len(page1.json()) == 2

    # Sayfalama: skip=2, limit=2
    page2 = client.get("/categories/?skip=2&limit=2")
    assert page2.status_code == 200
    assert len(page2.json()) == 2

    # Sayfalama: skip=4, limit=2 -> Son 1 kategori
    page3 = client.get("/categories/?skip=4&limit=2")
    assert page3.status_code == 200
    assert len(page3.json()) == 1


def test_get_category_by_id_success():
    """Mevcut bir kategorinin ID ile başarıyla getirildiği test edilir."""
    response = client.get("/categories/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Elektronik"


def test_get_category_by_id_not_found():
    """Olmayan bir kategori ID'si arandığında 404 döndüğü test edilir."""
    response = client.get("/categories/99999")
    assert response.status_code == 404


def test_update_category_success():
    """Kategori güncelleme (PUT /categories/{id}) test edilir."""
    payload = {
        "name": "Tüketici Elektroniği",
        "description": "Genişletilmiş açıklama."
    }
    response = client.put("/categories/1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == payload["name"]


def test_update_category_duplicate_name():
    """Kategori güncellenirken başka kategorinin ismi verilirse 409 döndüğü test edilir."""
    payload = {
        "name": "Mobilya",  # ID 2'ye ait isim
        "description": "Açıklama"
    }
    response = client.put("/categories/1", json=payload)
    assert response.status_code == 409


def test_delete_category_success():
    """Kategori silme (DELETE /categories/{id}) test edilir."""
    response = client.delete("/categories/1")
    assert response.status_code == 204

    # Tekrar arandığında 404 dönmeli
    get_res = client.get("/categories/1")
    assert get_res.status_code == 404


def test_delete_category_not_found():
    """Olmayan kategori silinmek istendiğinde 404 döndüğü test edilir."""
    response = client.delete("/categories/99999")
    assert response.status_code == 404
