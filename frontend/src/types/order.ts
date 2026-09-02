export type OrderStatus = 'PENDING' | 'CONFIRMED' | 'CANCELLED' | 'COMPLETED';

export interface OrderItem {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
}

export interface OrderItemCreate {
  product_id: number;
  quantity: number;
}

export interface Order {
  id: number;
  customer_email: string;
  total_amount: number;
  status: OrderStatus;
  items: OrderItem[];
  created_at: string;
}

export interface OrderCreate {
  customer_email: string;
  items: OrderItemCreate[];
}

export interface OrderStatusUpdate {
  status: OrderStatus;
}

export interface OrderFilterParams {
  customer_email?: string;
  status?: OrderStatus;
  skip?: number;
  limit?: number;
}
