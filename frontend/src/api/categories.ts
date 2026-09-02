import { apiClient } from './client';
import { Category, CategoryCreate, CategoryUpdate } from '../types/category';

export const categoriesApi = {
  getAll: async (skip = 0, limit = 100): Promise<Category[]> => {
    const response = await apiClient.get<Category[]>('/categories/', {
      params: { skip, limit },
    });
    return response.data;
  },

  getById: async (id: number): Promise<Category> => {
    const response = await apiClient.get<Category>(`/categories/${id}`);
    return response.data;
  },

  create: async (payload: CategoryCreate): Promise<Category> => {
    const response = await apiClient.post<Category>('/categories/', payload);
    return response.data;
  },

  update: async (id: number, payload: CategoryUpdate): Promise<Category> => {
    const response = await apiClient.put<Category>(`/categories/${id}`, payload);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/categories/${id}`);
  },
};
