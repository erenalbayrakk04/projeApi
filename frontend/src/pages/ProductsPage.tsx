import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productsApi } from '../api/products';
import { categoriesApi } from '../api/categories';
import { Product, ProductCreate, ProductFilterParams } from '../types/product';
import { ProductTable } from '../components/products/ProductTable';
import { ProductFilters } from '../components/products/ProductFilters';
import { ProductModal } from '../components/products/ProductModal';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';
import { PlusCircle, Package } from 'lucide-react';
import { toast } from 'sonner';

interface ProductsPageProps {
  isCreateOpen?: boolean;
  onCloseCreate?: () => void;
}

export const ProductsPage: React.FC<ProductsPageProps> = ({
  isCreateOpen = false,
  onCloseCreate,
}) => {
  const queryClient = useQueryClient();

  const [isModalOpen, setIsModalOpen] = useState(isCreateOpen);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [deletingProduct, setDeletingProduct] = useState<Product | null>(null);

  // Filters State
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | undefined>();
  const [minPrice, setMinPrice] = useState<number | undefined>();
  const [maxPrice, setMaxPrice] = useState<number | undefined>();
  const [isActiveFilter, setIsActiveFilter] = useState<boolean | undefined>();

  const filterParams: ProductFilterParams = {
    category_id: selectedCategoryId,
    min_price: minPrice,
    max_price: maxPrice,
    is_active: isActiveFilter,
    limit: 100,
  };

  const { data: rawProducts = [], isLoading: pLoading } = useQuery({
    queryKey: ['products', filterParams],
    queryFn: () => productsApi.getAll(filterParams),
  });

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.getAll(0, 100),
  });

  // Client-side search by name
  const filteredProducts = rawProducts.filter((p) => {
    if (!searchQuery.trim()) return true;
    return p.name.toLowerCase().includes(searchQuery.trim().toLowerCase());
  });

  const createMutation = useMutation({
    mutationFn: productsApi.create,
    onSuccess: (newProd) => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast.success(`'${newProd.name}' ürünü başarıyla oluşturuldu.`);
      setIsModalOpen(false);
      if (onCloseCreate) onCloseCreate();
    },
    onError: (err: any) => {
      toast.error(err.message || 'Ürün oluşturulurken hata meydana geldi.');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: ProductCreate }) =>
      productsApi.update(id, data),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast.success(`'${updated.name}' ürünü güncellendi.`);
      setIsModalOpen(false);
      setSelectedProduct(null);
    },
    onError: (err: any) => {
      toast.error(err.message || 'Ürün güncellenirken hata meydana geldi.');
    },
  });

  const toggleActiveMutation = useMutation({
    mutationFn: (product: Product) =>
      productsApi.patch(product.id, { is_active: !product.is_active }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast.success(`'${updated.name}' durumu ${updated.is_active ? 'Aktif' : 'Pasif'} yapıldı.`);
    },
    onError: (err: any) => {
      toast.error(err.message || 'Durum değiştirilemedi.');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => productsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast.success('Ürün başarıyla silindi.');
      setDeletingProduct(null);
    },
    onError: (err: any) => {
      toast.error(err.message || 'Ürün silinirken hata oluştu.');
    },
  });

  const handleOpenAdd = () => {
    setSelectedProduct(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (product: Product) => {
    setSelectedProduct(product);
    setIsModalOpen(true);
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedCategoryId(undefined);
    setMinPrice(undefined);
    setMaxPrice(undefined);
    setIsActiveFilter(undefined);
  };

  const handleFormSubmit = async (values: ProductCreate) => {
    if (selectedProduct) {
      await updateMutation.mutateAsync({
        id: selectedProduct.id,
        data: values,
      });
    } else {
      await createMutation.mutateAsync(values);
    }
  };

  const handleDeleteConfirm = async () => {
    if (deletingProduct) {
      await deleteMutation.mutateAsync(deletingProduct.id);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h3 className="text-base sm:text-lg font-bold text-slate-800 flex items-center gap-2">
            <Package className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>Ürün Kataloğu &amp; Envanter ({filteredProducts.length})</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Ürün fiyatları, stok kontrolleri, çoklu kategori atamaları ve durum yönetimi.
          </p>
        </div>
        <Button onClick={handleOpenAdd} leftIcon={<PlusCircle className="w-4 h-4" />} className="w-full sm:w-auto justify-center">
          Yeni Ürün Ekle
        </Button>
      </div>

      {/* Filters */}
      <ProductFilters
        categories={categories}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        selectedCategoryId={selectedCategoryId}
        onCategoryChange={setSelectedCategoryId}
        minPrice={minPrice}
        onMinPriceChange={setMinPrice}
        maxPrice={maxPrice}
        onMaxPriceChange={setMaxPrice}
        isActiveFilter={isActiveFilter}
        onIsActiveChange={setIsActiveFilter}
        onReset={handleResetFilters}
      />

      {/* Table */}
      {pLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-12 w-full rounded-xl" />
          <Skeleton className="h-16 w-full rounded-xl" count={5} />
        </div>
      ) : (
        <ProductTable
          products={filteredProducts}
          onEdit={handleOpenEdit}
          onDelete={setDeletingProduct}
          onToggleActive={(p) => toggleActiveMutation.mutate(p)}
          onAddNew={handleOpenAdd}
        />
      )}

      {/* Add / Edit Modal */}
      <ProductModal
        isOpen={isModalOpen || isCreateOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedProduct(null);
          if (onCloseCreate) onCloseCreate();
        }}
        onSubmit={handleFormSubmit}
        categories={categories}
        initialData={selectedProduct}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={Boolean(deletingProduct)}
        onClose={() => setDeletingProduct(null)}
        onConfirm={handleDeleteConfirm}
        title="Ürünü Sil"
        message={`'${deletingProduct?.name}' ürününü kalıcı olarak silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.`}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
};
