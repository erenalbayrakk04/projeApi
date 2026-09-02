import { apiClient } from './client';
import { HealthStatus } from '../types/common';

export const healthApi = {
  check: async (): Promise<HealthStatus> => {
    const response = await apiClient.get<HealthStatus>('/health');
    return response.data;
  },
};
