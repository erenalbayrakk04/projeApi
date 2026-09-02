"""
==============================================================================
Kategori Yönlendirici Katmanı (Category Router - HTTP Presentation Layer)
==============================================================================
Bu modül, /categories altındaki CRUD API endpoint'lerini tanımlar.
==============================================================================
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status

from schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)
from services.category_service import CategoryService, get_category_service

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={
        404: {"description": "Kategori bulunamadı (Not Found)."},
        409: {"description": "Aynı isimde kategori zaten mevcut (Conflict)."},
        422: {"description": "Pydantic doğrulama hatası (Unprocessable Entity)."},
    },
)


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni kategori oluştur",
    description="Sisteme yeni bir kategori kaydı ekler. Kategori adı benzersiz (unique) olmalıdır.",
)
def create_category(
    category_in: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    """
    Yeni kategori ekleme endpoint'i.
    - Aynı isimde kategori varsa **409 Conflict** döner.
    """
    try:
        return service.create_category(category_in)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        )


@router.get(
    "/",
    response_model=List[CategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Kategorileri listele",
    description="Sistemdeki tüm kategorileri sayfalama (skip/limit) desteğiyle listeler.",
)
def list_categories(
    skip: int = Query(default=0, ge=0, description="Atlanacak kayıt sayısı"),
    limit: int = Query(default=10, ge=1, le=100, description="Maksimum getirilecek kategori sayısı"),
    service: CategoryService = Depends(get_category_service),
) -> List[CategoryResponse]:
    """
    Kategori listesi getirme endpoint'i.
    """
    return service.list_categories(skip=skip, limit=limit)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="ID ile tekil kategori getir",
    description="Verilen benzersiz ID numarasına sahip kategoriyi getirir.",
)
def get_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    """
    ID ile kategori sorgulama endpoint'i:
    - Kategori bulunamazsa **404 Not Found** döner.
    """
    category = service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID numarası '{category_id}' olan kategori bulunamadı.",
        )
    return category


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Kategoriyi güncelle (PUT)",
    description="Belirtilen ID'deki kategorinin tüm alanlarını günceller.",
)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    """
    Kategori güncelleme endpoint'i:
    - Kategori yoksa **404 Not Found** döner.
    - Yeni isim başka bir kategoriye aitse **409 Conflict** döner.
    """
    try:
        updated = service.update_category(category_id, category_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Güncelleme başarısız: ID numarası '{category_id}' olan kategori bulunamadı.",
            )
        return updated
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        )


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Kategoriyi sil (DELETE)",
    description="Belirtilen ID'deki kategoriyi veritabanından kalıcı olarak siler.",
)
def delete_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service),
) -> None:
    """
    Kategori silme endpoint'i:
    - Başarılı silmede **204 No Content** döner.
    - Kategori yoksa **404 Not Found** döner.
    """
    success = service.delete_category(category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Silme başarısız: ID numarası '{category_id}' olan kategori bulunamadı.",
        )
    return None
