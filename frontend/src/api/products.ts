import { apiClient } from './client';
import {
  Product,
  ProductCreate,
  ProductUpdate,
  ProductPatch,
  ProductFilterParams,
} from '../types/product';

export const productsApi = {
  getAll: async (filters: ProductFilterParams = {}): Promise<Product[]> => {
    const params: Record<string, any> = {};

    if (filters.category) params.category = filters.category;
    if (filters.category_id) params.category_id = filters.category_id;
    if (filters.min_price !== undefined && filters.min_price !== null && !isNaN(filters.min_price)) {
      params.min_price = filters.min_price;
    }
    if (filters.max_price !== undefined && filters.max_price !== null && !isNaN(filters.max_price)) {
      params.max_price = filters.max_price;
    }
    if (filters.is_active !== undefined && filters.is_active !== null) {
      params.is_active = filters.is_active;
    }
    params.skip = filters.skip ?? 0;
    params.limit = filters.limit ?? 50;

    const response = await apiClient.get<Product[]>('/products/', { params });
    return response.data;
  },

  getById: async (id: number): Promise<Product> => {
    const response = await apiClient.get<Product>(`/products/${id}`);
    return response.data;
  },

  create: async (payload: ProductCreate): Promise<Product> => {
    const response = await apiClient.post<Product>('/products/', payload);
    return response.data;
  },

  update: async (id: number, payload: ProductUpdate): Promise<Product> => {
    const response = await apiClient.put<Product>(`/products/${id}`, payload);
    return response.data;
  },

  patch: async (id: number, payload: ProductPatch): Promise<Product> => {
    const response = await apiClient.patch<Product>(`/products/${id}`, payload);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/products/${id}`);
  },
};
