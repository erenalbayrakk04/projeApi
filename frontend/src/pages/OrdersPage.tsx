import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ordersApi } from '../api/orders';
import { productsApi } from '../api/products';
import { Order, OrderCreate, OrderStatus } from '../types/order';
import { OrderTable } from '../components/orders/OrderTable';
import { CreateOrderModal } from '../components/orders/CreateOrderModal';
import { OrderDetailModal } from '../components/orders/OrderDetailModal';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';
import { ShoppingCart, PlusCircle, Search, X } from 'lucide-react';
import { toast } from 'sonner';

interface OrdersPageProps {
  isCreateOpen?: boolean;
  onCloseCreate?: () => void;
}

export const OrdersPage: React.FC<OrdersPageProps> = ({
  isCreateOpen = false,
  onCloseCreate,
}) => {
  const queryClient = useQueryClient();

  const [isModalOpen, setIsModalOpen] = useState(isCreateOpen);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  // Filters
  const [emailSearch, setEmailSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<OrderStatus | undefined>();

  const { data: orders = [], isLoading: oLoading } = useQuery({
    queryKey: ['orders', { status: statusFilter }],
    queryFn: () => ordersApi.getAll({ status: statusFilter, limit: 100 }),
  });

  const { data: products = [] } = useQuery({
    queryKey: ['products'],
    queryFn: () => productsApi.getAll({ limit: 100 }),
  });

  const filteredOrders = orders.filter((o) => {
    if (!emailSearch.trim()) return true;
    return o.customer_email.toLowerCase().includes(emailSearch.trim().toLowerCase());
  });

  const createMutation = useMutation({
    mutationFn: ordersApi.create,
    onSuccess: (newOrder) => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast.success(`Sipariş #${newOrder.id} başarıyla oluşturuldu. Stoklar güncellendi.`);
      setIsModalOpen(false);
      if (onCloseCreate) onCloseCreate();
    },
    onError: (err: any) => {
      toast.error(err.message || 'Sipariş oluşturulamadı.');
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: OrderStatus }) =>
      ordersApi.updateStatus(id, status),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
      setSelectedOrder(updated);
      toast.success(`Sipariş #${updated.id} durumu '${updated.status}' olarak güncellendi.`);
    },
    onError: (err: any) => {
      toast.error(err.message || 'Sipariş durumu güncellenemedi.');
    },
  });

  const handleOpenDetail = (order: Order) => {
    setSelectedOrder(order);
    setIsDetailOpen(true);
  };

  const handleStatusChange = async (orderId: number, status: OrderStatus) => {
    await updateStatusMutation.mutateAsync({ id: orderId, status });
  };

  const handleFormSubmit = async (values: OrderCreate) => {
    await createMutation.mutateAsync(values);
  };

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <ShoppingCart className="w-5 h-5 text-emerald-600" />
            <span>Sipariş Listesi ({filteredOrders.length})</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Atomik stok düşümleri, fiyat hesaplamaları ve sipariş yaşam döngüsü.
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} leftIcon={<PlusCircle className="w-4 h-4" />}>
          Yeni Sipariş Oluştur
        </Button>
      </div>

      {/* Filters Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col sm:flex-row items-center gap-3 text-xs">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Müşteri e-posta adresine göre ara..."
            value={emailSearch}
            onChange={(e) => setEmailSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white outline-none focus:ring-2 focus:ring-emerald-400 text-xs"
          />
        </div>

        <div className="w-full sm:w-56">
          <select
            value={statusFilter || ''}
            onChange={(e) =>
              setStatusFilter(e.target.value ? (e.target.value as OrderStatus) : undefined)
            }
            className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white outline-none focus:ring-2 focus:ring-emerald-400 text-xs font-medium text-slate-700"
          >
            <option value="">Tüm Sipariş Durumları</option>
            <option value="PENDING">Beklemede (PENDING)</option>
            <option value="CONFIRMED">Onaylandı (CONFIRMED)</option>
            <option value="COMPLETED">Tamamlandı (COMPLETED)</option>
            <option value="CANCELLED">İptal Edildi (CANCELLED)</option>
          </select>
        </div>

        {(emailSearch || statusFilter) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setEmailSearch('');
              setStatusFilter(undefined);
            }}
            className="text-slate-400 hover:text-slate-600 shrink-0"
          >
            <X className="w-4 h-4 mr-1" /> Temizle
          </Button>
        )}
      </div>

      {/* Orders Table */}
      {oLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-12 w-full rounded-xl" />
          <Skeleton className="h-16 w-full rounded-xl" count={4} />
        </div>
      ) : (
        <OrderTable
          orders={filteredOrders}
          onViewDetails={handleOpenDetail}
          onStatusChange={handleStatusChange}
          onAddNew={() => setIsModalOpen(true)}
        />
      )}

      {/* Create Order Modal */}
      <CreateOrderModal
        isOpen={isModalOpen || isCreateOpen}
        onClose={() => {
          setIsModalOpen(false);
          if (onCloseCreate) onCloseCreate();
        }}
        onSubmit={handleFormSubmit}
        products={products}
        isLoading={createMutation.isPending}
      />

      {/* Order Detail Modal */}
      <OrderDetailModal
        order={selectedOrder}
        isOpen={isDetailOpen}
        onClose={() => {
          setIsDetailOpen(false);
          setSelectedOrder(null);
        }}
        products={products}
        onStatusChange={handleStatusChange}
        isStatusLoading={updateStatusMutation.isPending}
      />
    </div>
  );
};
