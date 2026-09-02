from .products import router as products_router
from .categories import router as categories_router
from .orders import router as orders_router

__all__ = ["products_router", "categories_router", "orders_router"]
