export interface HealthStatus {
  status: string;
  storage: string;
  total_active_records?: number;
  total_active_products?: number;
  total_categories?: number;
  total_orders?: number;
}

export interface ApiErrorResponse {
  detail?: string | Array<{ loc: (string | number)[]; msg: string; type: string }>;
}
