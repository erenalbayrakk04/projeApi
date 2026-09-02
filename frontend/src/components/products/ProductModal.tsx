import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Product, ProductCreate } from '../../types/product';
import { Category } from '../../types/category';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';

const productSchema = z.object({
  name: z.string().min(2, 'Ürün adı en az 2 karakter olmalıdır.').max(100),
  description: z.string().max(1000).optional().nullable(),
  price: z.coerce.number().positive('Fiyat 0\'dan büyük pozitif bir sayı olmalıdır.'),
  stock: z.coerce.number().int().nonnegative('Stok negatif olamaz.'),
  category_ids: z.array(z.number()).min(1, 'Lütfen en az 1 kategori seçiniz.'),
  is_active: z.boolean().default(true),
});

type ProductFormValues = z.infer<typeof productSchema>;

interface ProductModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (values: ProductCreate) => Promise<void>;
  categories: Category[];
  initialData?: Product | null;
  isLoading?: boolean;
}

export const ProductModal: React.FC<ProductModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  categories,
  initialData,
  isLoading = false,
}) => {
  const isEdit = Boolean(initialData);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<ProductFormValues>({
    resolver: zodResolver(productSchema),
    defaultValues: {
      name: '',
      description: '',
      price: 0,
      stock: 10,
      category_ids: [],
      is_active: true,
    },
  });

  const selectedCategoryIds = watch('category_ids') || [];

  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name,
        description: initialData.description || '',
        price: initialData.price,
        stock: initialData.stock,
        category_ids: initialData.category_ids || [],
        is_active: initialData.is_active,
      });
    } else {
      reset({
        name: '',
        description: '',
        price: 100,
        stock: 10,
        category_ids: categories.length > 0 ? [categories[0].id] : [],
        is_active: true,
      });
    }
  }, [initialData, categories, reset, isOpen]);

  const toggleCategory = (catId: number) => {
    if (selectedCategoryIds.includes(catId)) {
      setValue(
        'category_ids',
        selectedCategoryIds.filter((id) => id !== catId),
        { shouldValidate: true }
      );
    } else {
      setValue('category_ids', [...selectedCategoryIds, catId], {
        shouldValidate: true,
      });
    }
  };

  const handleFormSubmit = async (data: ProductFormValues) => {
    await onSubmit({
      name: data.name.trim(),
      description: data.description ? data.description.trim() : null,
      price: data.price,
      stock: data.stock,
      category_ids: data.category_ids,
      is_active: data.is_active,
    });
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? 'Ürünü Düzenle' : 'Yeni Ürün Ekle'}
      description="Ürün bilgilerini ve atanacağı kategorileri belirleyin."
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
        {/* Name */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
            Ürün Adı <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            placeholder="Örn: Kablosuz Mekanik Klavye"
            className={`w-full px-3.5 py-2 text-sm rounded-xl border bg-slate-50/50 focus:bg-white transition-all outline-none focus:ring-2 ${
              errors.name
                ? 'border-rose-300 focus:ring-rose-400'
                : 'border-slate-200 focus:border-emerald-500 focus:ring-emerald-400'
            }`}
            {...register('name')}
          />
          {errors.name && (
            <p className="text-xs text-rose-500 mt-1 font-medium">{errors.name.message}</p>
          )}
        </div>

        {/* Categories (Multi-select Badges) */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Kategoriler (Çoklu Seçim) <span className="text-rose-500">*</span>
          </label>
          <div className="flex flex-wrap gap-2 p-3 bg-slate-50/80 rounded-xl border border-slate-200">
            {categories.map((cat) => {
              const isSelected = selectedCategoryIds.includes(cat.id);
              return (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => toggleCategory(cat.id)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all border ${
                    isSelected
                      ? 'bg-emerald-600 text-white border-emerald-600 shadow-sm'
                      : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                  }`}
                >
                  {isSelected && '✓ '}
                  {cat.name}
                </button>
              );
            })}
          </div>
          {errors.category_ids && (
            <p className="text-xs text-rose-500 mt-1 font-medium">
              {errors.category_ids.message}
            </p>
          )}
        </div>

        {/* Price & Stock 2-Col */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
              Birim Fiyat (₺) <span className="text-rose-500">*</span>
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              placeholder="0.00"
              className={`w-full px-3.5 py-2 text-sm rounded-xl border bg-slate-50/50 focus:bg-white transition-all outline-none focus:ring-2 ${
                errors.price
                  ? 'border-rose-300 focus:ring-rose-400'
                  : 'border-slate-200 focus:border-emerald-500 focus:ring-emerald-400'
              }`}
              {...register('price')}
            />
            {errors.price && (
              <p className="text-xs text-rose-500 mt-1 font-medium">
                {errors.price.message}
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
              Stok Adedi <span className="text-rose-500">*</span>
            </label>
            <input
              type="number"
              min="0"
              placeholder="0"
              className={`w-full px-3.5 py-2 text-sm rounded-xl border bg-slate-50/50 focus:bg-white transition-all outline-none focus:ring-2 ${
                errors.stock
                  ? 'border-rose-300 focus:ring-rose-400'
                  : 'border-slate-200 focus:border-emerald-500 focus:ring-emerald-400'
              }`}
              {...register('stock')}
            />
            {errors.stock && (
              <p className="text-xs text-rose-500 mt-1 font-medium">
                {errors.stock.message}
              </p>
            )}
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
            Ürün Açıklaması (Opsiyonel)
          </label>
          <textarea
            rows={2}
            placeholder="Ürün özellikleri ve detayları..."
            className="w-full px-3.5 py-2 text-sm rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white transition-all outline-none focus:ring-2 focus:ring-emerald-400"
            {...register('description')}
          />
        </div>

        {/* Active Toggle */}
        <div className="flex items-center gap-2.5 pt-2">
          <input
            type="checkbox"
            id="is_active_toggle"
            className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500 border-slate-300 cursor-pointer"
            {...register('is_active')}
          />
          <label
            htmlFor="is_active_toggle"
            className="text-xs font-semibold text-slate-700 cursor-pointer"
          >
            Ürün satışa ve siparişe açık (Aktif)
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
          <Button variant="outline" type="button" onClick={onClose} disabled={isLoading}>
            İptal
          </Button>
          <Button type="submit" isLoading={isLoading}>
            {isEdit ? 'Değişiklikleri Kaydet' : 'Ürünü Ekle'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
