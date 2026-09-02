"""
==============================================================================
FastAPI Ana Uygulama Giriş Noktası (Main Application Entry Point)
==============================================================================
Bu dosya, FastAPI uygulamasının başlatıldığı, sunucu middleware (ara yazılım)
ayarlarının yapıldığı ve alt yönlendiricilerin (routers) sisteme dahil edildiği
merkezi yönetim dosyasıdır.

Temel Görevleri:
1. Lifespan Yönetimi: Sunucu açılırken (`startup`) ve kapanırken (`shutdown`)
   çalışacak yaşam döngüsü adımlarını asenkron context manager ile yönetir.
2. CORS Yapılandırması: Farklı domain/port'lardan (Frontend/React vb.) gelecek
   isteklerin tarayıcı güvenlik duvarına takılmasını önler.
3. Router Entegrasyonu: Modüler `products_router`, `categories_router` ve
   `orders_router` bileşenlerini uygulamaya bağlar.
4. Sistem Rotaları: Kök dizin (`/`) ve sistem sağlık kontrolü (`/health`) sunar.
==============================================================================
"""

import os
from contextlib import asynccontextmanager
import logging
from typing import Any, AsyncGenerator, Dict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from database import db, get_database
from routers.products import router as products_router
from routers.categories import router as categories_router
from routers.orders import router as orders_router


# ==============================================================================
# 1. Loglama Yapılandırması (Logging Configuration)
# ==============================================================================
# Sunucu hareketlerini tarih, log seviyesi ve mesaj şeklinde konsola yazdırır
logging.basicConfig(
    level=logging.INFO,  # INFO ve üstü seviyedeki tüm logları göster
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("product_api")  # Uygulamaya özel loglayıcı nesnesi


# ==============================================================================
# 2. Lifespan Yaşam Döngüsü Yöneticisi (Startup & Shutdown)
# ==============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI Lifespan Context Manager.
    Eski `@app.on_event("startup")` ve `@app.on_event("shutdown")` yapısının yerine
    geçen modern standarttır.

    - `yield` satırından ÖNCEKİ kodlar: Sunucu başlarken 1 kez çalışır.
    - `yield` satırından SONRAKİ kodlar: Sunucu kapatılırken 1 kez çalışır.
    """
    # ------------------ SUNUCU BAŞLATMA (STARTUP) ------------------
    logger.info("E-Commerce Management API sunucusu başlatılıyor...")

    # Başlangıçta test yapabilmeniz için örnek ürün ve kategori verilerini yükle
    active_db = get_database()
    active_db.seed_initial_data()
    db_type_name = "PostgreSQL" if "Postgres" in active_db.__class__.__name__ else "SQLite"
    logger.info(f"Örnek ürün ve kategori verileri {db_type_name} veritabanına başarıyla yüklendi.")

    # 'yield' ile kontrol FastAPI istek işleyicisine devredilir (Sunucu istek kabul eder)
    yield

    # ------------------ SUNUCU KAPANIŞ (SHUTDOWN) ------------------
    logger.info("E-Commerce Management API sunucusu kapatılıyor.")


# ==============================================================================
# 3. FastAPI Uygulamasının Oluşturulması
# ==============================================================================
app = FastAPI(
    title="E-Commerce & Product Management API",  # Swagger UI başlığı
    description="""
    🚀 **Production-Ready Thread-Safe SQLite E-Commerce & Product Management RESTful API**

    Bu API, **FastAPI**, **Pydantic v2** ve **Thread-Safe SQLite Veri Deposu**
    kullanılarak geliştirilmiş kurumsal standartlarda modüler bir servistir.

    ### 📌 Temel Modüller:
    * 📦 **Ürün Yönetimi (`/products`)**: Tam CRUD, kategori/fiyat filtreleme ve sayfalama.
    * 🏷️ **Kategori Yönetimi (`/categories`)**: Tam CRUD ve benzersiz isim denetimi.
    * 🛒 **Sipariş Yönetimi (`/orders`)**: Atomik sipariş oluşturma, otomatik stok düşümü/iadesi ve durum güncellemeleri.
    """,
    version="1.0.0",        # API sürümü
    docs_url="/docs",       # İnteraktif Swagger UI dökümantasyon adresi
    redoc_url="/redoc",     # Alternatif ReDoc dökümantasyon adresi
    lifespan=lifespan,      # Yaşam döngüsü yöneticisini bağla
)


# ==============================================================================
# 4. CORS (Cross-Origin Resource Sharing) Ara Yazılımı
# ==============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Tüm domainlerden gelen isteklere izin ver (Geliştirme için)
    allow_credentials=True,    # Kimlik doğrulama / Cookie paylaşımına izin ver
    allow_methods=["*"],       # Tüm HTTP metodlarına izin ver (GET, POST, PUT, DELETE vb.)
    allow_headers=["*"],       # Tüm özel başlıklara (headers) izin ver
)


# ==============================================================================
# 5. Router'ların Uygulamaya Kaydedilmesi
# ==============================================================================
# Rotaları ana FastAPI uygulamasına dahil et
app.include_router(products_router)
app.include_router(categories_router)
app.include_router(orders_router)


# ==============================================================================
# 6. Kök ve Sistem Durumu Endpoint'leri
# ==============================================================================
@app.get(
    "/",
    tags=["Root"],
    summary="API Hoş Geldiniz Bilgisi",
    status_code=status.HTTP_200_OK,
)
def root() -> Dict[str, Any]:
    """
    API kök dizinine (http://127.0.0.1:8000/) girildiğinde karşılama mesajı
    ve dökümantasyon linklerini döndürür.
    """
    return {
        "message": "Product Management RESTful API'ye Hoş Geldiniz!",
        "version": "1.0.0",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json",
        },
        "endpoints": {
            "products": "/products",
            "categories": "/categories",
            "orders": "/orders",
            "health": "/health",
        },
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Sistem Sağlık Kontrolü (Health Check)",
    status_code=status.HTTP_200_OK,
)
def health_check() -> Dict[str, Any]:
    """
    Servisin ve aktif veritabanının (SQLite / PostgreSQL) ayakta olup olmadığını kontrol eder.
    Toplam aktif ürün, kategori ve sipariş sayılarını dinamik olarak raporlar.
    """
    active_db = get_database()
    db_class = active_db.__class__.__name__
    storage_name = "PostgreSQL" if "Postgres" in db_class else "SQLite (products.db)"

    total_products = len(active_db.get_all())
    total_categories = len(active_db.get_all_categories())
    total_orders = len(active_db.get_all_orders())
    return {
        "status": "healthy",
        "storage": storage_name,
        "total_active_records": total_products,
        "total_categories": total_categories,
        "total_orders": total_orders,
    }


# ==============================================================================
# 7. Doğrudan Çalıştırma Bloğu (Direct Execution)
# ==============================================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
