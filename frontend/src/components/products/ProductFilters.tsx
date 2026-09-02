import React from 'react';
import { Category } from '../../types/category';
import { Search, X } from 'lucide-react';
import { Button } from '../ui/Button';

interface ProductFiltersProps {
  categories: Category[];
  searchQuery: string;
  onSearchChange: (q: string) => void;
  selectedCategoryId?: number;
  onCategoryChange: (catId?: number) => void;
  minPrice?: number;
  onMinPriceChange: (val?: number) => void;
  maxPrice?: number;
  onMaxPriceChange: (val?: number) => void;
  isActiveFilter?: boolean;
  onIsActiveChange: (val?: boolean) => void;
  onReset: () => void;
}

export const ProductFilters: React.FC<ProductFiltersProps> = ({
  categories,
  searchQuery,
  onSearchChange,
  selectedCategoryId,
  onCategoryChange,
  minPrice,
  onMinPriceChange,
  maxPrice,
  onMaxPriceChange,
  isActiveFilter,
  onIsActiveChange,
  onReset,
}) => {
  const isFiltered =
    searchQuery ||
    selectedCategoryId !== undefined ||
    minPrice !== undefined ||
    maxPrice !== undefined ||
    isActiveFilter !== undefined;

  return (
    <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
        {/* Search by Name */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Ürün adı ara..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white outline-none focus:ring-2 focus:ring-emerald-400 text-xs"
          />
        </div>

        {/* Category Filter */}
        <div>
          <select
            value={selectedCategoryId ?? ''}
            onChange={(e) =>
              onCategoryChange(e.target.value ? Number(e.target.value) : undefined)
            }
            className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white outline-none focus:ring-2 focus:ring-emerald-400 text-xs font-medium text-slate-700"
          >
            <option value="">Tüm Kategoriler</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
        </div>

        {/* Min Price */}
        <div>
          <input
            type="number"
            min="0"
            placeholder="Min Fiyat (₺)"
            value={minPrice ?? ''}
            onChange={(e) =>
              onMinPriceChange(e.target.value ? Number(e.target.value) : undefined)
            }
            className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white outline-none focus:ring-2 focus:ring-emerald-400 text-xs"
          />
        </div>

        {/* Max Price */}
        <div>
          <input
            type="number"
            min="0"
            placeholder="Max Fiyat (₺)"
            value={maxPrice ?? ''}
            onChange={(e) =>
              onMaxPriceChange(e.target.value ? Number(e.target.value) : undefined)
            }
            className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white outline-none focus:ring-2 focus:ring-emerald-400 text-xs"
          />
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <select
            value={
              isActiveFilter === undefined
                ? ''
                : isActiveFilter
                ? 'true'
                : 'false'
            }
            onChange={(e) => {
              if (e.target.value === '') onIsActiveChange(undefined);
              else onIsActiveChange(e.target.value === 'true');
            }}
            className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white outline-none focus:ring-2 focus:ring-emerald-400 text-xs font-medium text-slate-700"
          >
            <option value="">Tüm Durumlar</option>
            <option value="true">Sadece Aktif</option>
            <option value="false">Sadece Pasif</option>
          </select>

          {isFiltered && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onReset}
              title="Filtreleri Temizle"
              className="text-slate-400 hover:text-slate-600 px-2 shrink-0"
            >
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
