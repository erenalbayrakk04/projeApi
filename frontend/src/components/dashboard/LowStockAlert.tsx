import React from 'react';
import { Product } from '../../types/product';
import { AlertCircle } from 'lucide-react';
import { Badge } from '../ui/Badge';

interface LowStockAlertProps {
  products: Product[];
  onViewAll: () => void;
}

export const LowStockAlert: React.FC<LowStockAlertProps> = ({ products, onViewAll }) => {
  const lowStock = products.filter((p) => p.stock <= 10).slice(0, 5);

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-4 sm:p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-amber-500" />
          <h3 className="font-bold text-slate-800 text-sm">Kritik Stok Uyarıları (&le; 10 Adet)</h3>
        </div>
        <button
          onClick={onViewAll}
          className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 hover:underline"
        >
          Envantere Git &rarr;
        </button>
      </div>

      {lowStock.length === 0 ? (
        <p className="text-xs text-emerald-600 font-medium py-6 text-center bg-emerald-50/50 rounded-xl border border-emerald-100">
          Tüm ürünlerin stok seviyeleri güvenli durumda (&gt; 10 adet).
        </p>
      ) : (
        <div className="divide-y divide-slate-100">
          {lowStock.map((prod) => (
            <div key={prod.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 sm:gap-4 text-xs">
              <div>
                <span className="font-semibold text-slate-800">{prod.name}</span>
                <div className="flex items-center gap-1.5 mt-0.5">
                  {prod.categories.map((c) => (
                    <span key={c.id} className="text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                      {c.name}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center justify-between sm:justify-end gap-3 shrink-0">
                <span className="font-bold text-slate-700">
                  {prod.price.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                </span>
                {prod.stock === 0 ? (
                  <Badge variant="danger">Tükendi (0)</Badge>
                ) : (
                  <Badge variant="warning">{prod.stock} Adet Kaldı</Badge>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
