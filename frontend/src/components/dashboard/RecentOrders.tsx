import React from 'react';
import { Order } from '../../types/order';
import { Badge } from '../ui/Badge';
import { ShoppingCart } from 'lucide-react';

interface RecentOrdersProps {
  orders: Order[];
  onViewAll: () => void;
}

export const RecentOrders: React.FC<RecentOrdersProps> = ({ orders, onViewAll }) => {
  const recent = orders.slice(0, 5);

  const getStatusBadge = (status: Order['status']) => {
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
    <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <ShoppingCart className="w-5 h-5 text-slate-600" />
          <h3 className="font-bold text-slate-800 text-sm">Son Siparişler</h3>
        </div>
        <button
          onClick={onViewAll}
          className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 hover:underline"
        >
          Tümünü Gör ({orders.length}) &rarr;
        </button>
      </div>

      {recent.length === 0 ? (
        <p className="text-xs text-slate-400 py-6 text-center">Henüz sipariş kaydı bulunmuyor.</p>
      ) : (
        <div className="divide-y divide-slate-100">
          {recent.map((order) => (
            <div key={order.id} className="py-3 flex items-center justify-between text-xs">
              <div>
                <span className="font-bold text-slate-800">#{order.id}</span>
                <span className="text-slate-400 mx-1.5">&bull;</span>
                <span className="text-slate-600 font-medium">{order.customer_email}</span>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  {new Date(order.created_at).toLocaleString('tr-TR')}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-bold text-slate-800">
                  {order.total_amount.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                </span>
                {getStatusBadge(order.status)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
