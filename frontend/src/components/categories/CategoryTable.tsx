import React from 'react';
import { Category } from '../../types/category';
import { Edit2, Trash2, Calendar, Tag } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';

interface CategoryTableProps {
  categories: Category[];
  onEdit: (category: Category) => void;
  onDelete: (category: Category) => void;
  onAddNew: () => void;
}

export const CategoryTable: React.FC<CategoryTableProps> = ({
  categories,
  onEdit,
  onDelete,
  onAddNew,
}) => {
  if (categories.length === 0) {
    return (
      <EmptyState
        title="Henüz Kategori Bulunmuyor"
        description="Ürünleri sınıflandırmak ve ilişkileri yönetmek için yeni bir kategori oluşturun."
        actionText="Yeni Kategori Ekle"
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
              <th className="py-3.5 px-6">Kategori Adı</th>
              <th className="py-3.5 px-6">Açıklama</th>
              <th className="py-3.5 px-6">Oluşturulma Tarihi</th>
              <th className="py-3.5 px-6 text-right">Eylemler</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {categories.map((category) => (
              <tr key={category.id} className="hover:bg-slate-50/50 transition-colors">
                <td className="py-3.5 px-6 font-mono font-bold text-slate-500">
                  #{category.id}
                </td>
                <td className="py-3.5 px-6">
                  <div className="flex items-center gap-2">
                    <Tag className="w-4 h-4 text-emerald-500 shrink-0" />
                    <span className="font-bold text-slate-800 text-sm">
                      {category.name}
                    </span>
                  </div>
                </td>
                <td className="py-3.5 px-6 text-slate-500 max-w-xs truncate">
                  {category.description || <span className="text-slate-300 italic">Açıklama yok</span>}
                </td>
                <td className="py-3.5 px-6 text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>{new Date(category.created_at).toLocaleString('tr-TR')}</span>
                  </div>
                </td>
                <td className="py-3.5 px-6 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    <button
                      onClick={() => onEdit(category)}
                      title="Düzenle"
                      className="p-1.5 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => onDelete(category)}
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
