import React from 'react';
import { Package, Tags, ShoppingCart, TrendingUp } from 'lucide-react';
import { Product } from '../../types/product';
import { Category } from '../../types/category';
import { Order } from '../../types/order';

interface StatsCardsProps {
  products: Product[];
  categories: Category[];
  orders: Order[];
}

export const StatsCards: React.FC<StatsCardsProps> = ({
  products,
  categories,
  orders,
}) => {
  const totalRevenue = orders
    .filter((o) => o.status !== 'CANCELLED')
    .reduce((sum, o) => sum + o.total_amount, 0);

  const activeProducts = products.filter((p) => p.is_active).length;

  const cards = [
    {
      title: 'Aktif Ürünler',
      value: `${activeProducts} / ${products.length}`,
      subtitle: `${products.length - activeProducts} pasif ürün`,
      icon: Package,
      gradient: 'from-emerald-500 to-teal-600',
      lightBg: 'bg-emerald-50 text-emerald-600',
    },
    {
      title: 'Toplam Kategori',
      value: categories.length,
      subtitle: 'Tanımlı sınıflandırma',
      icon: Tags,
      gradient: 'from-blue-500 to-indigo-600',
      lightBg: 'bg-blue-50 text-blue-600',
    },
    {
      title: 'Toplam Sipariş',
      value: orders.length,
      subtitle: `${orders.filter((o) => o.status === 'COMPLETED').length} tamamlanan`,
      icon: ShoppingCart,
      gradient: 'from-violet-500 to-purple-600',
      lightBg: 'bg-violet-50 text-violet-600',
    },
    {
      title: 'Toplam Ciro',
      value: `${totalRevenue.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺`,
      subtitle: 'İptaller hariç net ciro',
      icon: TrendingUp,
      gradient: 'from-amber-500 to-orange-600',
      lightBg: 'bg-amber-50 text-amber-600',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between hover:shadow-md transition-shadow"
          >
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                {card.title}
              </p>
              <h3 className="text-2xl font-bold text-slate-800 mt-1">
                {card.value}
              </h3>
              <p className="text-xs text-slate-400 mt-1 font-medium">
                {card.subtitle}
              </p>
            </div>
            <div
              className={`w-12 h-12 rounded-2xl flex items-center justify-center ${card.lightBg}`}
            >
              <Icon className="w-6 h-6" />
            </div>
          </div>
        );
      })}
    </div>
  );
};
