import React, { useState } from 'react';
import { Layout } from './components/layout/Layout';
import { NavTab } from './components/layout/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { ProductsPage } from './pages/ProductsPage';
import { CategoriesPage } from './pages/CategoriesPage';
import { OrdersPage } from './pages/OrdersPage';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard');
  const [isProductCreateOpen, setIsProductCreateOpen] = useState(false);
  const [isOrderCreateOpen, setIsOrderCreateOpen] = useState(false);

  const handleQuickNewProduct = () => {
    setCurrentTab('products');
    setIsProductCreateOpen(true);
  };

  const handleQuickNewOrder = () => {
    setCurrentTab('orders');
    setIsOrderCreateOpen(true);
  };

  return (
    <Layout currentTab={currentTab} onSelectTab={setCurrentTab}>
      {currentTab === 'dashboard' && (
        <DashboardPage
          onNavigate={setCurrentTab}
          onOpenNewProduct={handleQuickNewProduct}
          onOpenNewOrder={handleQuickNewOrder}
        />
      )}

      {currentTab === 'products' && (
        <ProductsPage
          isCreateOpen={isProductCreateOpen}
          onCloseCreate={() => setIsProductCreateOpen(false)}
        />
      )}

      {currentTab === 'categories' && <CategoriesPage />}

      {currentTab === 'orders' && (
        <OrdersPage
          isCreateOpen={isOrderCreateOpen}
          onCloseCreate={() => setIsOrderCreateOpen(false)}
        />
      )}
    </Layout>
  );
};
export default App;
