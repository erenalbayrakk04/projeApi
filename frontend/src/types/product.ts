import { Category } from './category';

export interface Product {
  id: number;
  name: string;
  description: string | null;
  price: number;
  stock: number;
  is_active: boolean;
  category_ids: number[];
  categories: Category[];
  created_at: string;
}

export interface ProductCreate {
  name: string;
  description?: string | null;
  price: number;
  stock: number;
  category_ids: number[];
  is_active?: boolean;
}

export interface ProductUpdate {
  name: string;
  description?: string | null;
  price: number;
  stock: number;
  category_ids: number[];
  is_active?: boolean;
}

export interface ProductPatch {
  name?: string;
  description?: string | null;
  price?: number;
  stock?: number;
  category_ids?: number[];
  is_active?: boolean;
}

export interface ProductFilterParams {
  category?: string;
  category_id?: number;
  min_price?: number;
  max_price?: number;
  is_active?: boolean;
  skip?: number;
  limit?: number;
}
