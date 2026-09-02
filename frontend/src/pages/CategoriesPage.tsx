import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { categoriesApi } from '../api/categories';
import { Category, CategoryCreate } from '../types/category';
import { CategoryTable } from '../components/categories/CategoryTable';
import { CategoryModal } from '../components/categories/CategoryModal';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';
import { PlusCircle, Tags } from 'lucide-react';
import { toast } from 'sonner';

export const CategoriesPage: React.FC = () => {
  const queryClient = useQueryClient();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [deletingCategory, setDeletingCategory] = useState<Category | null>(null);

  const { data: categories = [], isLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.getAll(0, 100),
  });

  const createMutation = useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: (newCat) => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast.success(`'${newCat.name}' kategorisi başarıyla eklendi.`);
      setIsModalOpen(false);
    },
    onError: (err: any) => {
      toast.error(err.message || 'Kategori eklenirken hata oluştu.');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: CategoryCreate }) =>
      categoriesApi.update(id, data),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast.success(`'${updated.name}' kategorisi güncellendi.`);
      setIsModalOpen(false);
      setSelectedCategory(null);
    },
    onError: (err: any) => {
      toast.error(err.message || 'Kategori güncellenirken hata oluştu.');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => categoriesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast.success('Kategori başarıyla silindi.');
      setDeletingCategory(null);
    },
    onError: (err: any) => {
      toast.error(err.message || 'Kategori silinirken hata oluştu.');
    },
  });

  const handleOpenAdd = () => {
    setSelectedCategory(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (category: Category) => {
    setSelectedCategory(category);
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (values: CategoryCreate) => {
    if (selectedCategory) {
      await updateMutation.mutateAsync({
        id: selectedCategory.id,
        data: values,
      });
    } else {
      await createMutation.mutateAsync(values);
    }
  };

  const handleDeleteConfirm = async () => {
    if (deletingCategory) {
      await deleteMutation.mutateAsync(deletingCategory.id);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <Tags className="w-5 h-5 text-emerald-600" />
            <span>Kategori Listesi ({categories.length})</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Ürünlere atanabilecek benzersiz kategori tanımları ve detayları.
          </p>
        </div>
        <Button onClick={handleOpenAdd} leftIcon={<PlusCircle className="w-4 h-4" />}>
          Yeni Kategori Ekle
        </Button>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-12 w-full rounded-xl" />
          <Skeleton className="h-16 w-full rounded-xl" count={4} />
        </div>
      ) : (
        <CategoryTable
          categories={categories}
          onEdit={handleOpenEdit}
          onDelete={setDeletingCategory}
          onAddNew={handleOpenAdd}
        />
      )}

      {/* Add / Edit Modal */}
      <CategoryModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedCategory(null);
        }}
        onSubmit={handleFormSubmit}
        initialData={selectedCategory}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deletingCategory)}
        onClose={() => setDeletingCategory(null)}
        onConfirm={handleDeleteConfirm}
        title="Kategoriyi Sil"
        message={`'${deletingCategory?.name}' kategorisini kalıcı olarak silmek istediğinizden emin misiniz?`}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
};
