import React from 'react';
import { Order, OrderStatus } from '../../types/order';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Eye, Calendar, Mail } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';

interface OrderTableProps {
  orders: Order[];
  onViewDetails: (order: Order) => void;
  onStatusChange?: (orderId: number, status: OrderStatus) => void;
  onAddNew: () => void;
}

export const OrderTable: React.FC<OrderTableProps> = ({
  orders,
  onViewDetails,
  onAddNew,
}) => {
  if (orders.length === 0) {
    return (
      <EmptyState
        title="Henüz Sipariş Kaydı Bulunmuyor"
        description="Müşteriler için yeni sipariş oluşturabilir ve stok düşümlerini test edebilirsiniz."
        actionText="Yeni Sipariş Oluştur"
        onAction={onAddNew}
      />
    );
  }

  const getStatusBadge = (status: OrderStatus) => {
    switch (status) {
      case 'PENDING':
        return <Badge variant="warning">Beklemede</Badge>;
      case 'CONFIRMED':
        return <Badge variant="info">Onaylandı</Badge>;
      case 'COMPLETED':
        return <Badge variant="success">Tamamlandı</Badge>;
      case 'CANCELLED':
        return <Badge variant="danger">İptal Edildi</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/80 border-b border-slate-200/80 text-[11px] font-bold uppercase tracking-wider text-slate-500">
              <th className="py-3.5 px-6">Sipariş ID</th>
              <th className="py-3.5 px-6">Müşteri E-Posta</th>
              <th className="py-3.5 px-6">Kalem Adedi</th>
              <th className="py-3.5 px-6">Toplam Tutar</th>
              <th className="py-3.5 px-6">Durum</th>
              <th className="py-3.5 px-6">Tarih</th>
              <th className="py-3.5 px-6 text-right">Eylemler</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {orders.map((order) => (
              <tr key={order.id} className="hover:bg-slate-50/50 transition-colors">
                <td className="py-3.5 px-6 font-mono font-bold text-slate-700">
                  #{order.id}
                </td>
                <td className="py-3.5 px-6">
                  <div className="flex items-center gap-2 font-medium text-slate-800">
                    <Mail className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{order.customer_email}</span>
                  </div>
                </td>
                <td className="py-3.5 px-6">
                  <span className="px-2 py-0.5 rounded bg-slate-100 font-semibold text-slate-600">
                    {order.items.reduce((s, i) => s + i.quantity, 0)} Ürün
                  </span>
                </td>
                <td className="py-3.5 px-6">
                  <span className="font-bold text-slate-800 text-sm">
                    {order.total_amount.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                  </span>
                </td>
                <td className="py-3.5 px-6">
                  <div className="flex items-center gap-2">
                    {getStatusBadge(order.status)}
                  </div>
                </td>
                <td className="py-3.5 px-6 text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>{new Date(order.created_at).toLocaleString('tr-TR')}</span>
                  </div>
                </td>
                <td className="py-3.5 px-6 text-right">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onViewDetails(order)}
                    leftIcon={<Eye className="w-3.5 h-3.5" />}
                  >
                    Detay
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
