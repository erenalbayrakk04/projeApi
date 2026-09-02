export interface Category {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export interface CategoryCreate {
  name: string;
  description?: string | null;
}

export interface CategoryUpdate {
  name: string;
  description?: string | null;
}
