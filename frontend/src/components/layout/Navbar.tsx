import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../../api/health';
import { RefreshCw, Menu } from 'lucide-react';
import { NavTab } from './Sidebar';

interface NavbarProps {
  currentTab: NavTab;
  onOpenMobileMenu?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onOpenMobileMenu }) => {
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
      subtitle: 'Ürün kataloğu, stok kontrolleri ve filtreler',
    },
    categories: {
      title: 'Kategori Yönetimi',
      subtitle: 'Ürün sınıflandırma etiketleri ve benzersiz kategoriler',
    },
    orders: {
      title: 'Sipariş Yönetimi',
      subtitle: 'Müşteri siparişleri ve atomik stok düşümleri',
    },
  };

  const currentInfo = tabTitles[currentTab];

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-4 sm:px-6 lg:px-8 flex items-center justify-between sticky top-0 z-20 shadow-sm/50">
      {/* Sol: Hamburger Butonu (Mobil) + Başlık */}
      <div className="flex items-center gap-3 min-w-0">
        {onOpenMobileMenu && (
          <button
            onClick={onOpenMobileMenu}
            className="lg:hidden p-2 -ml-1 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors shrink-0"
            title="Menüyü Aç"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        <div className="min-w-0">
          <h2 className="text-sm sm:text-base font-bold text-slate-800 tracking-tight truncate">
            {currentInfo.title}
          </h2>
          <p className="text-[11px] sm:text-xs text-slate-500 font-normal hidden sm:block truncate">
            {currentInfo.subtitle}
          </p>
        </div>
      </div>

      {/* Sağ: Backend Sağlık Rozeti */}
      <div className="flex items-center gap-2 sm:gap-4 shrink-0">
        <div
          onClick={() => refetch()}
          title="Sağlık durumunu yenilemek için tıklayın"
          className="cursor-pointer flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1.5 rounded-full border bg-slate-50/80 hover:bg-slate-100/80 transition-all text-xs select-none"
        >
          {isLoading ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 text-slate-400 animate-spin" />
              <span className="text-slate-500 font-medium text-[11px] sm:text-xs">
                Kontrol...
              </span>
            </>
          ) : isError ? (
            <>
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
              <span className="text-rose-600 font-semibold text-[11px] sm:text-xs">
                Çevrimdışı
              </span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
              <span className="text-emerald-700 font-medium text-[11px] sm:text-xs">
                <span className="hidden sm:inline">FastAPI: </span>
                <span className="font-semibold text-emerald-800">{health?.status}</span>
                <span className="hidden md:inline text-slate-400"> ({health?.storage})</span>
              </span>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
