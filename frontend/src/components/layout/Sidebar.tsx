import React, { useEffect } from 'react';
import {
  LayoutDashboard,
  Package,
  Tags,
  ShoppingCart,
  BookOpen,
  Store,
  X,
} from 'lucide-react';

export type NavTab = 'dashboard' | 'products' | 'categories' | 'orders';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  isOpenMobile?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  isOpenMobile = false,
  onCloseMobile,
}) => {
  const navItems = [
    { id: 'dashboard' as NavTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'products' as NavTab, label: 'Ürün Yönetimi', icon: Package },
    { id: 'categories' as NavTab, label: 'Kategoriler', icon: Tags },
    { id: 'orders' as NavTab, label: 'Siparişler', icon: ShoppingCart },
  ];

  // Mobil menü açıkken ESC tuşu ile kapatma
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpenMobile && onCloseMobile) {
        onCloseMobile();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpenMobile, onCloseMobile]);

  // Sidebar İçerik Bloğu (Ortak)
  const sidebarContent = (
    <div className="flex flex-col h-full bg-slate-900 text-slate-300">
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-6 border-b border-slate-800 bg-slate-950/40">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-900/30 shrink-0">
            <Store className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-wide">ProjeApi</h1>
            <p className="text-[11px] text-emerald-400 font-medium">E-Commerce SPA</p>
          </div>
        </div>

        {/* Mobilde Kapatma Butonu */}
        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="lg:hidden p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
            title="Menüyü Kapat"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Nav Menu */}
      <div className="flex-1 py-6 px-3 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Yönetim Paneli
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => {
                onSelectTab(item.id);
                if (onCloseMobile) onCloseMobile();
              }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-emerald-600/10 text-emerald-400 border border-emerald-500/20 shadow-sm'
                  : 'hover:bg-slate-800/60 hover:text-white text-slate-300'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Footer Info & API Docs Link */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/20 space-y-3">
        <a
          href="/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-between w-full px-3 py-2 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-xs text-slate-300 transition-colors border border-slate-700/60"
        >
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-emerald-400" />
            <span className="font-medium">FastAPI Docs</span>
          </div>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
            Swagger
          </span>
        </a>
        <div className="text-[11px] text-slate-400 text-center">
          FastAPI &amp; React 18 &bull; v1.1.0
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* 1. Masaüstü Sabit Sidebar (lg ve üzeri) */}
      <aside className="hidden lg:flex w-64 flex-col shrink-0 h-screen sticky top-0 border-r border-slate-800">
        {sidebarContent}
      </aside>

      {/* 2. Mobil / Tablet Slide-over Çekmece (lg altı) */}
      {isOpenMobile && (
        <div className="fixed inset-0 z-50 lg:hidden">
          {/* Karartmalı Arka Plan (Backdrop) */}
          <div
            className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs transition-opacity animate-in fade-in"
            onClick={onCloseMobile}
          />
          {/* Çekmece Menü */}
          <div className="fixed inset-y-0 left-0 w-72 max-w-[85vw] shadow-2xl border-r border-slate-800 z-10 animate-in slide-in-from-left duration-200">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
