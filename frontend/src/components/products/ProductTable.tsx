import React from 'react';
import { Product } from '../../types/product';
import { Badge } from '../ui/Badge';
import { Edit2, Trash2, CheckCircle2, XCircle } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';

interface ProductTableProps {
  products: Product[];
  onEdit: (product: Product) => void;
  onDelete: (product: Product) => void;
  onToggleActive: (product: Product) => void;
  onAddNew: () => void;
}

export const ProductTable: React.FC<ProductTableProps> = ({
  products,
  onEdit,
  onDelete,
  onToggleActive,
  onAddNew,
}) => {
  if (products.length === 0) {
    return (
      <EmptyState
        title="Aranan Kriterlere Uygun Ürün Bulunamadı"
        description="Filtreleri temizleyebilir veya yeni bir ürün ekleyebilirsiniz."
        actionText="Yeni Ürün Ekle"
        onAction={onAddNew}
      />
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/80 border-b border-slate-200/80 text-[11px] font-bold uppercase tracking-wider text-slate-500">
              <th className="py-3.5 px-6">ID</th>
              <th className="py-3.5 px-6">Ürün Bilgisi</th>
              <th className="py-3.5 px-6">Kategoriler</th>
              <th className="py-3.5 px-6">Birim Fiyat</th>
              <th className="py-3.5 px-6">Stok Durumu</th>
              <th className="py-3.5 px-6">Aktiflik</th>
              <th className="py-3.5 px-6 text-right">Eylemler</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {products.map((product) => (
              <tr key={product.id} className="hover:bg-slate-50/50 transition-colors">
                <td className="py-3.5 px-6 font-mono font-bold text-slate-400">
                  #{product.id}
                </td>
                <td className="py-3.5 px-6">
                  <div>
                    <span className="font-bold text-slate-800 text-sm">
                      {product.name}
                    </span>
                    {product.description && (
                      <p className="text-[11px] text-slate-400 truncate max-w-xs mt-0.5">
                        {product.description}
                      </p>
                    )}
                  </div>
                </td>
                <td className="py-3.5 px-6">
                  <div className="flex flex-wrap gap-1 max-w-xs">
                    {product.categories && product.categories.length > 0 ? (
                      product.categories.map((c) => (
                        <span
                          key={c.id}
                          className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[10px] font-semibold border border-slate-200"
                        >
                          {c.name}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-300 italic text-[10px]">Kategorisiz</span>
                    )}
                  </div>
                </td>
                <td className="py-3.5 px-6">
                  <span className="font-bold text-slate-800 text-sm">
                    {product.price.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                  </span>
                </td>
                <td className="py-3.5 px-6">
                  {product.stock === 0 ? (
                    <Badge variant="danger">Tükendi (0)</Badge>
                  ) : product.stock <= 10 ? (
                    <Badge variant="warning">{product.stock} Adet (Kritik)</Badge>
                  ) : (
                    <span className="font-semibold text-slate-700">{product.stock} Adet</span>
                  )}
                </td>
                <td className="py-3.5 px-6">
                  <button
                    onClick={() => onToggleActive(product)}
                    className="flex items-center gap-1.5 cursor-pointer hover:opacity-80 transition-opacity"
                    title="Durumu değiştirmek için tıklayın"
                  >
                    {product.is_active ? (
                      <>
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        <Badge variant="success">Aktif</Badge>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-4 h-4 text-slate-400" />
                        <Badge variant="neutral">Pasif</Badge>
                      </>
                    )}
                  </button>
                </td>
                <td className="py-3.5 px-6 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    <button
                      onClick={() => onEdit(product)}
                      title="Düzenle"
                      className="p-1.5 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => onDelete(product)}
                      title="Sil"
                      className="p-1.5 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
