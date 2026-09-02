"""
==============================================================================
Ürün Yönlendirici Katmanı (Product Router - HTTP Presentation Layer)
==============================================================================
Bu modül, istemciden (Frontend, Mobil, Swagger UI) gelen HTTP isteklerini karşılar,
URL yollarını (Endpoints) tanımlar ve sonuçları uygun HTTP durum kodlarıyla döndürür.
==============================================================================
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductPatch,
    ProductResponse,
)
from services.product_service import ProductService, get_product_service


router = APIRouter(
    prefix="/products",
    tags=["Products"],
    responses={
        404: {"description": "Aranan ürün veya kategori bulunamadı (Not Found)."},
        400: {"description": "Geçersiz istek parametresi (Bad Request)."},
        422: {"description": "Pydantic şema doğrulama hatası (Unprocessable Entity)."},
    },
)


# ==============================================================================
# 1. YENİ ÜRÜN OLUŞTURMA ENDPOINT'İ (POST /products/)
# ==============================================================================
@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni ürün oluştur",
    description="Gelen verileri doğrular ve seçilen kategori ID'leri ile birlikte yeni bir ürün kaydeder.",
)
def create_product(
    product_in: ProductCreate,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """
    Yeni ürün ekleme fonksiyonu:
    - Belirtilen `category_ids` içindeki ID'lerden biri sistemde yoksa **404 Not Found** döner.
    """
    try:
        return service.create_product(product_in)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        )


# ==============================================================================
# 2. ÜRÜNLERİ LİSTELEME VE FİLTRELEME ENDPOINT'İ (GET /products/)
# ==============================================================================
@router.get(
    "/",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Ürünleri filtrele ve listele",
    description="Tüm ürünleri listeler. Kategori ismi, Kategori ID'si, fiyat aralığı, aktiflik durumu ve sayfalama destekler.",
)
def list_products(
    category: Optional[str] = Query(
        default=None,
        description="Filtrelenecek kategori adı (büyük/küçük harf duyarsız)",
        examples=["Elektronik"],
    ),
    category_id: Optional[int] = Query(
        default=None,
        ge=1,
        description="Filtrelenecek kategori ID numarası",
        examples=[1],
    ),
    min_price: Optional[float] = Query(
        default=None,
        ge=0,
        description="Minimum ürün fiyatı",
        examples=[1000.0],
    ),
    max_price: Optional[float] = Query(
        default=None,
        ge=0,
        description="Maksimum ürün fiyatı",
        examples=[5000.0],
    ),
    is_active: Optional[bool] = Query(
        default=None,
        description="Ürünün satışta olup olmadığına göre filtrele (True/False)",
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Sayfalama için baştan atlanacak kayıt sayısı (Offset)",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Tek seferde getirilecek maksimum kayıt sayısı (1 ile 100 arası)",
    ),
    service: ProductService = Depends(get_product_service),
) -> List[ProductResponse]:
    """
    Filtreli ürün listesi getirme fonksiyonu:
    - Eğer `min_price > max_price` ise **400 Bad Request** fırlatır.
    """
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filtreleme hatası: 'min_price' değeri 'max_price' değerinden büyük olamaz.",
        )

    return service.get_products(
        category=category,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


# ==============================================================================
# 3. ID İLE TEKİL ÜRÜN GETİRME ENDPOINT'İ (GET /products/{product_id})
# ==============================================================================
@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="ID ile tekil ürün getir",
    description="Verilen benzersiz ürün ID'sine göre ürünün tüm detaylarını ve dahil olduğu kategorileri getirir.",
)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """
    ID ile ürün getirme:
    - Ürün bulunamazsa **404 Not Found** hatası fırlatır.
    """
    product = service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID numarası '{product_id}' olan ürün sistemde bulunamadı.",
        )
    return product


# ==============================================================================
# 4. TAM GÜNCELLEME ENDPOINT'İ (PUT /products/{product_id})
# ==============================================================================
@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Ürünü tamamen güncelle (PUT)",
    description="Belirtilen ID'deki ürünün tüm alanlarını ve kategori ilişkilerini yeni verilerle tamamen değiştirir.",
)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """
    Tam güncelleme (PUT):
    - Ürün veya kategori ID'si bulunamazsa **404 Not Found** döner.
    """
    try:
        updated = service.update_product(product_id, product_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Güncelleme başarısız: ID numarası '{product_id}' olan ürün bulunamadı.",
            )
        return updated
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        )


# ==============================================================================
# 5. KISMİ GÜNCELLEME ENDPOINT'İ (PATCH /products/{product_id})
# ==============================================================================
@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Ürünü kısmi güncelle (PATCH)",
    description="Belirtilen ID'deki ürünün yalnızca gönderilen belirli alanlarını ve/veya kategori ilişkilerini günceller.",
)
def patch_product(
    product_id: int,
    product_in: ProductPatch,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """
    Kısmi güncelleme (PATCH):
    - Ürün bulunamazsa **404 Not Found** döner.
    """
    try:
        patched = service.patch_product(product_id, product_in)
        if not patched:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Kısmi güncelleme başarısız: ID numarası '{product_id}' olan ürün bulunamadı.",
            )
        return patched
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        )


# ==============================================================================
# 6. ÜRÜN SİLME ENDPOINT'İ (DELETE /products/{product_id})
# ==============================================================================
@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Ürünü sil (DELETE)",
    description="Belirtilen ID'deki ürünü ve kategori ilişkilerini veritabanından kalıcı olarak siler.",
)
def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
) -> None:
    """
    Ürün silme (DELETE):
    - Ürün başarıyla silinirse HTTP **204 No Content** döner.
    - Ürün bulunamazsa **404 Not Found** döner.
    """
    success = service.delete_product(product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Silme başarısız: ID numarası '{product_id}' olan ürün bulunamadı.",
        )
    return None
