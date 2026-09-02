import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../../api/health';
import { RefreshCw } from 'lucide-react';
import { NavTab } from './Sidebar';

interface NavbarProps {
  currentTab: NavTab;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab }) => {
  const { data: health, isLoading, isError, refetch } = useQuery({
    queryKey: ['health'],
    queryFn: healthApi.check,
    refetchInterval: 15000,
  });

  const tabTitles: Record<NavTab, { title: string; subtitle: string }> = {
    dashboard: {
      title: 'Genel Bakış & Metrikler',
      subtitle: 'Sistem istatistikleri, aktif ürünler ve son siparişler',
    },
    products: {
      title: 'Ürün Yönetimi',
      subtitle: 'Ürün kataloğu, stok kontrolleri, çoklu kategori atamaları ve fiyat filtreleri',
    },
    categories: {
      title: 'Kategori Yönetimi',
      subtitle: 'Ürün sınıflandırma etiketleri ve benzersiz kategori tanımları',
    },
    orders: {
      title: 'Sipariş Yönetimi',
      subtitle: 'Müşteri siparişleri, atomik stok düşümleri ve durum yönetimi',
    },
  };

  const currentInfo = tabTitles[currentTab];

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-8 flex items-center justify-between sticky top-0 z-20 shadow-sm/50">
      <div>
        <h2 className="text-base font-bold text-slate-800 tracking-tight">
          {currentInfo.title}
        </h2>
        <p className="text-xs text-slate-500 font-normal">{currentInfo.subtitle}</p>
      </div>

      <div className="flex items-center gap-4">
        {/* Backend Health Status Pill */}
        <div
          onClick={() => refetch()}
          title="Sağlık durumunu yenilemek için tıklayın"
          className="cursor-pointer flex items-center gap-2 px-3 py-1.5 rounded-full border bg-slate-50/80 hover:bg-slate-100/80 transition-all text-xs select-none"
        >
          {isLoading ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 text-slate-400 animate-spin" />
              <span className="text-slate-500 font-medium">Kontrol ediliyor...</span>
            </>
          ) : isError ? (
            <>
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
              <span className="text-rose-600 font-semibold">Backend Çevrimdışı</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-emerald-700 font-medium">
                FastAPI: <span className="font-semibold text-emerald-800">{health?.status}</span> ({health?.storage})
              </span>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
