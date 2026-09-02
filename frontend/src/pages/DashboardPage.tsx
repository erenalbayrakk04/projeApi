import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { productsApi } from '../api/products';
import { categoriesApi } from '../api/categories';
import { ordersApi } from '../api/orders';
import { StatsCards } from '../components/dashboard/StatsCards';
import { RecentOrders } from '../components/dashboard/RecentOrders';
import { LowStockAlert } from '../components/dashboard/LowStockAlert';
import { Skeleton } from '../components/ui/Skeleton';
import { NavTab } from '../components/layout/Sidebar';
import { Button } from '../components/ui/Button';
import { PlusCircle, ShoppingBag } from 'lucide-react';

interface DashboardPageProps {
  onNavigate: (tab: NavTab) => void;
  onOpenNewProduct: () => void;
  onOpenNewOrder: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onNavigate,
  onOpenNewProduct,
  onOpenNewOrder,
}) => {
  const { data: products = [], isLoading: pLoading } = useQuery({
    queryKey: ['products'],
    queryFn: () => productsApi.getAll({ limit: 100 }),
  });

  const { data: categories = [], isLoading: cLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.getAll(0, 100),
  });

  const { data: orders = [], isLoading: oLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: () => ordersApi.getAll({ limit: 100 }),
  });

  const isLoading = pLoading || cLoading || oLoading;

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 to-slate-800 text-white p-6 rounded-2xl shadow-sm border border-slate-700/50">
        <div>
          <h2 className="text-xl font-bold tracking-tight">Hoş Geldiniz! 👋</h2>
          <p className="text-xs text-slate-300 mt-1 max-w-lg">
            FastAPI RESTful mimarisine bağlı ürün, çoklu kategori ve sipariş yönetim paneli.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenNewProduct}
            leftIcon={<PlusCircle className="w-4 h-4 text-emerald-400" />}
            className="bg-slate-800 text-white border-slate-700 hover:bg-slate-700"
          >
            Yeni Ürün
          </Button>
          <Button
            size="sm"
            onClick={onOpenNewOrder}
            leftIcon={<ShoppingBag className="w-4 h-4" />}
          >
            Yeni Sipariş Ver
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
          <Skeleton className="h-28 rounded-2xl" count={4} />
        </div>
      ) : (
        <StatsCards
          products={products}
          categories={categories}
          orders={orders}
        />
      )}

      {/* 2-Column Grid for Recent Orders & Low Stock */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {isLoading ? (
          <>
            <Skeleton className="h-64 rounded-2xl" />
            <Skeleton className="h-64 rounded-2xl" />
          </>
        ) : (
          <>
            <RecentOrders orders={orders} onViewAll={() => onNavigate('orders')} />
            <LowStockAlert products={products} onViewAll={() => onNavigate('products')} />
          </>
        )}
      </div>
    </div>
  );
};
