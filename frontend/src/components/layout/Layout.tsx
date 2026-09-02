import React from 'react';
import { Sidebar, NavTab } from './Sidebar';
import { Navbar } from './Navbar';

interface LayoutProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({
  currentTab,
  onSelectTab,
  children,
}) => {
  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sol Sidebar */}
      <Sidebar currentTab={currentTab} onSelectTab={onSelectTab} />

      {/* Sağ Ana İçerik */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar currentTab={currentTab} />
        <main className="flex-1 p-8 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
};
