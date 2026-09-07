import React from 'react';
import {
  LayoutDashboard,
  Package,
  Tags,
  ShoppingCart,
  BookOpen,
  Store,
} from 'lucide-react';

export type NavTab = 'dashboard' | 'products' | 'categories' | 'orders';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const navItems = [
    { id: 'dashboard' as NavTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'products' as NavTab, label: 'Ürün Yönetimi', icon: Package },
    { id: 'categories' as NavTab, label: 'Kategoriler', icon: Tags },
    { id: 'orders' as NavTab, label: 'Siparişler', icon: ShoppingCart },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 h-screen sticky top-0 border-r border-slate-800">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 gap-3 border-b border-slate-800 bg-slate-950/40">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-900/30">
          <Store className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-white tracking-wide">ProjeApi</h1>
          <p className="text-[11px] text-emerald-400 font-medium">E-Commerce SPA</p>
        </div>
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
              onClick={() => onSelectTab(item.id)}
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
    </aside>
  );
};
