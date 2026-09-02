import React from 'react';
import { Order, OrderStatus } from '../../types/order';
import { Product } from '../../types/product';
import { Modal } from '../ui/Modal';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Calendar, Mail, Package } from 'lucide-react';

interface OrderDetailModalProps {
  order: Order | null;
  isOpen: boolean;
  onClose: () => void;
  products: Product[];
  onStatusChange: (orderId: number, newStatus: OrderStatus) => Promise<void>;
  isStatusLoading?: boolean;
}

export const OrderDetailModal: React.FC<OrderDetailModalProps> = ({
  order,
  isOpen,
  onClose,
  products,
  onStatusChange,
  isStatusLoading = false,
}) => {
  if (!order) return null;

  const getProductName = (productId: number) => {
    const p = products.find((prod) => prod.id === productId);
    return p ? p.name : `Ürün #${productId}`;
  };

  const getStatusBadge = (status: OrderStatus) => {
    switch (status) {
      case 'PENDING':
        return <Badge variant="warning">Beklemede (PENDING)</Badge>;
      case 'CONFIRMED':
        return <Badge variant="info">Onaylandı (CONFIRMED)</Badge>;
      case 'COMPLETED':
        return <Badge variant="success">Tamamlandı (COMPLETED)</Badge>;
      case 'CANCELLED':
        return <Badge variant="danger">İptal Edildi (CANCELLED)</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Sipariş Detayı #${order.id}`}
      description="Sipariş kalemleri, müşteri bilgisi ve durum yönetimi."
      maxWidth="lg"
    >
      <div className="space-y-6">
        {/* Info Grid */}
        <div className="grid grid-cols-2 gap-4 p-4 bg-slate-50 rounded-2xl border border-slate-200 text-xs">
          <div className="space-y-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Müşteri E-Posta
            </span>
            <div className="flex items-center gap-1.5 font-semibold text-slate-800">
              <Mail className="w-3.5 h-3.5 text-slate-400" />
              <span>{order.customer_email}</span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Sipariş Tarihi
            </span>
            <div className="flex items-center gap-1.5 text-slate-600">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>{new Date(order.created_at).toLocaleString('tr-TR')}</span>
            </div>
          </div>
        </div>

        {/* Order Items Table */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
            <Package className="w-4 h-4 text-emerald-600" />
            <span>Sipariş Kalemleri ({order.items.length})</span>
          </h4>

          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px]">
                <tr>
                  <th className="py-2.5 px-4">Ürün</th>
                  <th className="py-2.5 px-4 text-center">Adet</th>
                  <th className="py-2.5 px-4 text-right">Birim Fiyat</th>
                  <th className="py-2.5 px-4 text-right">Ara Toplam</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {order.items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/50">
                    <td className="py-3 px-4 font-semibold text-slate-800">
                      {getProductName(item.product_id)}
                      <span className="text-[10px] text-slate-400 block font-normal font-mono">
                        Ürün ID: #{item.product_id}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-bold text-slate-700">
                      {item.quantity} Adet
                    </td>
                    <td className="py-3 px-4 text-right font-medium text-slate-600">
                      {item.unit_price.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-slate-800">
                      {(item.quantity * item.unit_price).toLocaleString('tr-TR', {
                        minimumFractionDigits: 2,
                      })}{' '}
                      ₺
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-slate-50/80 border-t border-slate-200 font-bold">
                <tr>
                  <td colSpan={3} className="py-3 px-4 text-right text-slate-600 uppercase text-[11px]">
                    Genel Toplam Tutar:
                  </td>
                  <td className="py-3 px-4 text-right text-emerald-700 text-sm font-extrabold">
                    {order.total_amount.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        {/* Status Change Controls */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Güncel Durum:
            </span>
            {getStatusBadge(order.status)}
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-200">
            <span className="text-xs text-slate-500 font-medium">Durumu Değiştir:</span>
            {(['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'] as OrderStatus[]).map(
              (statusKey) => (
                <button
                  key={statusKey}
                  disabled={order.status === statusKey || isStatusLoading}
                  onClick={() => onStatusChange(order.id, statusKey)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all ${
                    order.status === statusKey
                      ? 'bg-slate-800 text-white border-slate-800 opacity-60 cursor-not-allowed'
                      : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300 hover:bg-slate-100'
                  }`}
                >
                  {statusKey}
                </button>
              )
            )}
          </div>
          <p className="text-[11px] text-slate-400 italic">
            * Sipariş CANCELLED yapıldığında ürün stokları otomatik olarak geri iade edilir.
          </p>
        </div>

        <div className="flex justify-end pt-2">
          <Button variant="outline" onClick={onClose}>
            Kapat
          </Button>
        </div>
      </div>
    </Modal>
  );
};
