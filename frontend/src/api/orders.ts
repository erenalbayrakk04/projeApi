import { apiClient } from './client';
import {
  Order,
  OrderCreate,
  OrderStatus,
  OrderFilterParams,
} from '../types/order';

export const ordersApi = {
  getAll: async (filters: OrderFilterParams = {}): Promise<Order[]> => {
    const params: Record<string, any> = {};

    if (filters.customer_email) params.customer_email = filters.customer_email;
    if (filters.status) params.status = filters.status;
    params.skip = filters.skip ?? 0;
    params.limit = filters.limit ?? 50;

    const response = await apiClient.get<Order[]>('/orders/', { params });
    return response.data;
  },

  getById: async (id: number): Promise<Order> => {
    const response = await apiClient.get<Order>(`/orders/${id}`);
    return response.data;
  },

  create: async (payload: OrderCreate): Promise<Order> => {
    const response = await apiClient.post<Order>('/orders/', payload);
    return response.data;
  },

  updateStatus: async (id: number, status: OrderStatus): Promise<Order> => {
    const response = await apiClient.patch<Order>(`/orders/${id}/status`, { status });
    return response.data;
  },
};
