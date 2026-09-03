"""
==============================================================================
SQLAlchemy Sipariş Deposu (Order Repository)
==============================================================================
Cosmic Python Repository Pattern standardında Sipariş veri erişim deposu.
ACID transaction, stok düşümü ve iptal halinde stok iadesi operasyonlarını yönetir.
==============================================================================
"""

from typing import Any, Callable, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from interfaces.repositories import IOrderRepository
from adapters.sqlalchemy.models import OrderItemModel, OrderModel, ProductModel


class SqlAlchemyOrderRepository(IOrderRepository):
    """
    SQLAlchemy oturumu üzerinden atomik sipariş operasyonlarını yürüten depo.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory

    def create_order_atomic(
        self,
        customer_email: str,
        items_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Atomik olarak siparişi kaydeder, ürün stoklarını düşer ve sipariş kalemlerini ekler.
        """
        with self.session_factory() as session:
            try:
                total_amount = 0.0
                order_items = []

                for item in items_data:
                    prod_id = item["product_id"]
                    req_qty = item["quantity"]

                    # Ürünü bul
                    product = session.get(ProductModel, prod_id)
                    if not product:
                        raise ValueError(f"ID'si {prod_id} olan ürün bulunamadı.")

                    if not product.is_active:
                        raise ValueError(f"'{product.name}' ürünü satışta/aktif değildir.")

                    if product.stock < req_qty:
                        raise ValueError(
                            f"'{product.name}' için Yetersiz stok. Mevcut: {product.stock}, Talep: {req_qty}"
                        )

                    unit_price = float(product.price)
                    total_amount += unit_price * req_qty

                    # Stok düşümü
                    product.stock -= req_qty

                    order_item = OrderItemModel(
                        product_id=prod_id,
                        quantity=req_qty,
                        unit_price=unit_price,
                    )
                    order_items.append(order_item)

                order = OrderModel(
                    customer_email=customer_email.strip(),
                    total_amount=round(total_amount, 2),
                    status="PENDING",
                    items=order_items,
                )
                session.add(order)
                session.commit()
                session.refresh(order)
                return order.to_dict()
            except Exception:
                session.rollback()
                raise

    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """ID numarasına göre siparişi kalemleriyle birlikte getirir."""
        with self.session_factory() as session:
            order = session.get(OrderModel, order_id)
            return order.to_dict() if order else None

    def get_all_orders(
        self,
        customer_email: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Siparişleri opsiyonel filtre kriterleriyle listeler."""
        with self.session_factory() as session:
            query = session.query(OrderModel)

            if customer_email is not None:
                query = query.filter(
                    func.lower(OrderModel.customer_email) == func.lower(customer_email.strip())
                )

            if status is not None:
                query = query.filter(
                    func.upper(OrderModel.status) == func.upper(status.strip())
                )

            orders = query.order_by(OrderModel.id.desc()).all()
            return [o.to_dict() for o in orders]

    def update_order_status_atomic(self, order_id: int, new_status: str) -> Optional[Dict[str, Any]]:
        """Sipariş durumunu günceller ve iptal halinde stoğu iade eder."""
        target_status = new_status.strip().upper()

        with self.session_factory() as session:
            try:
                order = session.get(OrderModel, order_id)
                if not order:
                    return None

                previous_status = order.status

                if previous_status == target_status:
                    return order.to_dict()

                # İptal edilirse stoğu iade et
                if target_status == "CANCELLED" and previous_status != "CANCELLED":
                    for item in order.items:
                        product = session.get(ProductModel, item.product_id)
                        if product:
                            product.stock += item.quantity

                # İptalden geri çıkartılırsa stoğu tekrar kontrol et ve düş
                elif previous_status == "CANCELLED" and target_status != "CANCELLED":
                    for item in order.items:
                        product = session.get(ProductModel, item.product_id)
                        if not product or product.stock < item.quantity:
                            current_stk = product.stock if product else 0
                            raise ValueError(
                                f"Stok yetersizliği nedeniyle sipariş iptalden çıkartılamıyor: "
                                f"'{product.name if product else 'Ürün'}' için mevcut stok {current_stk}, "
                                f"gerekli adet {item.quantity}."
                            )
                        product.stock -= item.quantity

                order.status = target_status
                session.commit()
                session.refresh(order)
                return order.to_dict()
            except Exception:
                session.rollback()
                raise
