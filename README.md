# 🚀 Product Management In-Memory RESTful API

FastAPI ve Pydantic v2 kullanılarak geliştirilmiş, **Thread-Safe In-Memory** depolama mimarisine sahip, production-ready standartlarında modüler RESTful API.

---

## 📁 Proje Dosya Yapısı

```text
c:\projeApi\
│
├── database.py              # Thread-safe in-memory veritabanı (Lock, CRUD & Seed Data)
├── main.py                  # FastAPI uygulaması, CORS, Lifespan yönetimi ve Router'lar
├── requirements.txt         # Proje bağımlılıkları
├── README.md                # Proje dökümantasyonu ve kullanım kılavuzu
│
├── schemas/                 # Pydantic v2 veri şemaları ve validasyonlar
│   ├── __init__.py
│   └── product.py           # ProductBase, Create, Update, Patch, Response şemaları
│
├── services/                # İş mantığı (Business Logic) ve servis katmanı
│   ├── __init__.py
│   └── product_service.py   # ProductService & get_product_service Dependency Provider
│
├── routers/                 # API Endpoint yönlendirmeleri
│   ├── __init__.py
│   └── products.py          # /products endpoint'leri (CRUD & filtreleme)
│
└── tests/                   # Pytest birim ve entegrasyon testleri
    ├── __init__.py
    └── test_products.py     # 23 adet kapsamlı test (validasyonlar, CRUD, filtreler, thread-safety)
```

---

## 🛠️ Mimari ve Öne Çıkan Özellikler

1. **Pydantic v2 Modelleri:**
   - `ProductBase`, `ProductCreate`, `ProductUpdate` (PUT), `ProductPatch` (PATCH) ve `ProductResponse` olarak net şekilde ayrıştırılmış şemalar.
   - Detaylı alan doğrulamaları (`min_length=2`, `gt=0`, `ge=0`), örnek veriler (`json_schema_extra`) ve `ConfigDict(from_attributes=True)`.

2. **Thread-Safe In-Memory Storage:**
   - Eşzamanlı (concurrent) isteklerde veri tutarsızlığını ve yarış durumlarını (*race condition*) önlemek için `threading.Lock` ile korunan `InMemoryDatabase` yapısı.
   - Otomatik artan ID ve UTC zaman damgalı `created_at` ataması.

3. **Katmanlı & Modüler Mimari:**
   - **Router Katmanı:** HTTP isteklerini, durum kodlarını (`201`, `200`, `204`, `404`, `400`, `422`) ve girdi/çıktı şemalarını yönetir.
   - **Servis Katmanı:** İş mantığı, filtreleme, sayfalama ve veri dönüşümlerini yürütür.
   - **Veri Katmanı:** Bellek üzerindeki veri depolama işlemlerini soyutlar.
   - **Dependency Injection:** FastAPI `Depends(get_product_service)` mekanizması ile zayıf bağlılık (*loose coupling*) ve kolay test edilebilirlik.

4. **Gelişmiş Filtreleme & Sayfalama:**
   - Kategoriye göre büyük/küçük harf duyarsız filtreleme (`category`).
   - Fiyat aralığı filtreleme (`min_price`, `max_price`) ve mantıksal doğrulama (`min_price <= max_price`).
   - Aktiflik durumuna göre filtreleme (`is_active`).
   - Sayfalama desteği (`skip` ve `limit`).

---

## ⚙️ Kurulum ve Çalıştırma

### 1. Gereksinimlerin Yüklenmesi

Projeyi çalıştırmadan önce bağımlılıkları yükleyin:

```bash
pip install -r requirements.txt
```

### 2. Uygulamanın Başlatılması (Uvicorn)

Geliştirme sunucusunu otomatik yeniden yükleme (*hot-reload*) moduyla başlatmak için:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Alternatif olarak doğrudan `main.py` dosyasını çalıştırabilirsiniz:

```bash
python main.py
```

---

## 🌐 Canlı Dökümantasyon Bağlantıları

Uygulama ayağa kalktığında aşağıdaki adreslerden erişebilirsiniz:

- **Swagger UI (İnteraktif API Dökümantasyonu):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc (Alternatif Temiz Dökümantasyon):** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON Spesifikasyonu:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 📡 API Endpoint'leri ve Örnek İstekler

| Metot | Endpoint | Durum Kodu | Açıklama |
|---|---|---|---|
| `POST` | `/products/` | `201 Created` | Yeni ürün oluşturma |
| `GET` | `/products/` | `200 OK` | Ürünleri listeleme, filtreleme ve sayfalama |
| `GET` | `/products/{product_id}` | `200 OK` / `404` | ID'ye göre tekil ürün getirme |
| `PUT` | `/products/{product_id}` | `200 OK` / `404` | Ürünü tamamen güncelleme |
| `PATCH` | `/products/{product_id}` | `200 OK` / `404` | Ürünü kısmi güncelleme |
| `DELETE`| `/products/{product_id}` | `204 No Content` / `404` | Ürünü silme |
| `GET` | `/health` | `200 OK` | Sistem sağlık durumu ve kayıt sayısı |

---

### 💡 Örnek cURL Komutları

#### 1. Yeni Ürün Ekleme (POST)
```bash
curl -X POST "http://127.0.0.1:8000/products/" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Kablosuz Gaming Mouse",
       "description": "26000 DPI optik sensörlü şarjlı oyuncu faresi",
       "price": 1450.00,
       "stock": 20,
       "category": "Elektronik",
       "is_active": true
     }'
```

#### 2. Ürünleri Filtreleme ve Sayfalama (GET)
```bash
# Elektronik kategorisinde, 1000 - 5000 TL arasındaki ilk 5 ürünü listele
curl -X GET "http://127.0.0.1:8000/products/?category=Elektronik&min_price=1000&max_price=5000&skip=0&limit=5"
```

#### 3. ID ile Tekil Ürün Getirme (GET)
```bash
curl -X GET "http://127.0.0.1:8000/products/1"
```

#### 4. Ürünü Tam Güncelleme (PUT)
```bash
curl -X PUT "http://127.0.0.1:8000/products/1" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Kablosuz Mekanik Klavye V2",
       "description": "RGB Aydınlatmalı ve Bilek Destekli Model",
       "price": 2100.00,
       "stock": 15,
       "category": "Elektronik",
       "is_active": true
     }'
```

#### 5. Ürünü Kısmi Güncelleme (PATCH)
```bash
curl -X PATCH "http://127.0.0.1:8000/products/1" \
     -H "Content-Type: application/json" \
     -d '{
       "price": 1950.00,
       "stock": 30
     }'
```

#### 6. Ürünü Silme (DELETE)
```bash
curl -X DELETE "http://127.0.0.1:8000/products/1"
```

---

## 🧪 Testlerin Çalıştırılması

Proje için hazırlanmış 23 adet birim, entegrasyon, validasyon ve eşzamanlılık (thread-safety) testini çalıştırmak için:

```bash
pytest -v
```
