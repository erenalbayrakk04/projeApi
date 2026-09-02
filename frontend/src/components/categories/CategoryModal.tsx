import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Category, CategoryCreate } from '../../types/category';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';

const categorySchema = z.object({
  name: z
    .string()
    .min(2, 'Kategori adı en az 2 karakter olmalıdır.')
    .max(100, 'Kategori adı en fazla 100 karakter olabilir.'),
  description: z.string().max(1000, 'Açıklama 1000 karakteri geçemez.').optional().nullable(),
});

type CategoryFormValues = z.infer<typeof categorySchema>;

interface CategoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (values: CategoryCreate) => Promise<void>;
  initialData?: Category | null;
  isLoading?: boolean;
}

export const CategoryModal: React.FC<CategoryModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  isLoading = false,
}) => {
  const isEdit = Boolean(initialData);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CategoryFormValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: {
      name: '',
      description: '',
    },
  });

  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name,
        description: initialData.description || '',
      });
    } else {
      reset({
        name: '',
        description: '',
      });
    }
  }, [initialData, reset, isOpen]);

  const handleFormSubmit = async (data: CategoryFormValues) => {
    await onSubmit({
      name: data.name.trim(),
      description: data.description ? data.description.trim() : null,
    });
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? 'Kategoriyi Düzenle' : 'Yeni Kategori Ekle'}
      description="Kategori adı veritabanında benzersiz (unique) olmalıdır."
    >
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
            Kategori Adı <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            placeholder="Örn: Elektronik, Mobilya, Gaming"
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

        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
            Açıklama (Opsiyonel)
          </label>
          <textarea
            rows={3}
            placeholder="Kategori hakkında kısa bir açıklama yazın..."
            className={`w-full px-3.5 py-2 text-sm rounded-xl border bg-slate-50/50 focus:bg-white transition-all outline-none focus:ring-2 ${
              errors.description
                ? 'border-rose-300 focus:ring-rose-400'
                : 'border-slate-200 focus:border-emerald-500 focus:ring-emerald-400'
            }`}
            {...register('description')}
          />
          {errors.description && (
            <p className="text-xs text-rose-500 mt-1 font-medium">
              {errors.description.message}
            </p>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
          <Button variant="outline" type="button" onClick={onClose} disabled={isLoading}>
            İptal
          </Button>
          <Button type="submit" isLoading={isLoading}>
            {isEdit ? 'Güncelle' : 'Oluştur'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
