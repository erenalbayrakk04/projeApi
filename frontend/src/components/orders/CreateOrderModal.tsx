import React from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Product } from '../../types/product';
import { OrderCreate } from '../../types/order';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Plus, Trash2, ShoppingBag } from 'lucide-react';

const orderItemSchema = z.object({
  product_id: z.coerce.number().positive('Geçerli bir ürün seçiniz.'),
  quantity: z.coerce.number().int().positive('Adet en az 1 olmalıdır.'),
});

const orderSchema = z.object({
  customer_email: z.string().email('Geçerli bir e-posta adresi giriniz.'),
  items: z.array(orderItemSchema).min(1, 'Siparişe en az 1 ürün kalemi eklemelisiniz.'),
});

type OrderFormValues = z.infer<typeof orderSchema>;

interface CreateOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (values: OrderCreate) => Promise<void>;
  products: Product[];
  isLoading?: boolean;
}

export const CreateOrderModal: React.FC<CreateOrderModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  products,
  isLoading = false,
}) => {
  const activeProducts = products.filter((p) => p.is_active);

  const {
    register,
    control,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<OrderFormValues>({
    resolver: zodResolver(orderSchema),
    defaultValues: {
      customer_email: '',
      items: [{ product_id: activeProducts[0]?.id || 1, quantity: 1 }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'items',
  });

  const watchedItems = watch('items') || [];

  // Canlı Toplam Tutar Hesabı
  const calculatedTotal = watchedItems.reduce((sum, item) => {
    const matchedProduct = products.find((p) => p.id === Number(item.product_id));
    if (!matchedProduct) return sum;
    const qty = Number(item.quantity) || 0;
    return sum + matchedProduct.price * qty;
  }, 0);

  const handleFormSubmit = async (data: OrderFormValues) => {
    await onSubmit({
      customer_email: data.customer_email.trim(),
      items: data.items.map((i) => ({
        product_id: Number(i.product_id),
        quantity: Number(i.quantity),
      })),
    });
    reset();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Yeni Sipariş Oluştur"
      description="Ürünleri sepete ekleyin; stoklar atomik olarak düşülecektir."
      maxWidth="xl"
    >
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-5">
        {/* Customer Email */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
            Müşteri E-Posta Adresi <span className="text-rose-500">*</span>
          </label>
          <input
            type="email"
            placeholder="ornek@musteri.com"
            className={`w-full px-3.5 py-2 text-sm rounded-xl border bg-slate-50/50 focus:bg-white transition-all outline-none focus:ring-2 ${
              errors.customer_email
                ? 'border-rose-300 focus:ring-rose-400'
                : 'border-slate-200 focus:border-emerald-500 focus:ring-emerald-400'
            }`}
            {...register('customer_email')}
          />
          {errors.customer_email && (
            <p className="text-xs text-rose-500 mt-1 font-medium">
              {errors.customer_email.message}
            </p>
          )}
        </div>

        {/* Dynamic Order Items */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
              Sipariş Kalemleri ({fields.length})
            </label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => append({ product_id: activeProducts[0]?.id || 1, quantity: 1 })}
              leftIcon={<Plus className="w-3.5 h-3.5" />}
            >
              Kalem Ekle
            </Button>
          </div>

          <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
            {fields.map((field, idx) => {
              const currentProductId = Number(watchedItems[idx]?.product_id);
              const currentProduct = products.find((p) => p.id === currentProductId);
              const currentQty = Number(watchedItems[idx]?.quantity) || 0;
              const isOverStock = currentProduct && currentQty > currentProduct.stock;

              return (
                <div
                  key={field.id}
                  className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex flex-col sm:flex-row items-start sm:items-center gap-3 text-xs"
                >
                  {/* Product Select */}
                  <div className="flex-1 w-full">
                    <select
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white font-medium text-slate-800 outline-none focus:ring-2 focus:ring-emerald-400"
                      {...register(`items.${idx}.product_id` as const)}
                    >
                      {activeProducts.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} — {p.price.toLocaleString('tr-TR')} ₺ (Stok: {p.stock})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Quantity Stepper */}
                  <div className="w-28 flex flex-col">
                    <input
                      type="number"
                      min="1"
                      placeholder="Adet"
                      className={`w-full px-3 py-2 rounded-lg border bg-white font-semibold outline-none focus:ring-2 ${
                        isOverStock
                          ? 'border-rose-400 focus:ring-rose-400 text-rose-600'
                          : 'border-slate-200 focus:ring-emerald-400'
                      }`}
                      {...register(`items.${idx}.quantity` as const)}
                    />
                  </div>

                  {/* Item Subtotal */}
                  <div className="w-24 text-right font-bold text-slate-700">
                    {currentProduct
                      ? `${(currentProduct.price * currentQty).toLocaleString('tr-TR', {
                          minimumFractionDigits: 2,
                        })} ₺`
                      : '0.00 ₺'}
                  </div>

                  {/* Remove Button */}
                  {fields.length > 1 && (
                    <button
                      type="button"
                      onClick={() => remove(idx)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
                      title="Kalemi Sil"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          {errors.items && (
            <p className="text-xs text-rose-500 font-medium">{errors.items.message}</p>
          )}
        </div>

        {/* Live Total Summary Card */}
        <div className="p-4 bg-emerald-50/70 border border-emerald-200 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-800">
              Tahmini Toplam Tutar
            </span>
            <p className="text-[11px] text-emerald-600">Fiyatlar veritabanından güvenle hesaplanır</p>
          </div>
          <span className="text-xl font-extrabold text-emerald-800">
            {calculatedTotal.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
          </span>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Button variant="outline" type="button" onClick={onClose} disabled={isLoading}>
            İptal
          </Button>
          <Button
            type="submit"
            isLoading={isLoading}
            leftIcon={<ShoppingBag className="w-4 h-4" />}
          >
            Siparişi Onayla &amp; Oluştur
          </Button>
        </div>
      </form>
    </Modal>
  );
};
