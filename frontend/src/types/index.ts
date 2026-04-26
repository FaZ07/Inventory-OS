// ── Auth ─────────────────────────────────────────────────────────────────────

export type UserRole = "admin" | "warehouse_manager" | "supplier" | "viewer";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// ── Pagination ────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ── Product ───────────────────────────────────────────────────────────────────

export type ProductCategory =
  | "electronics" | "clothing" | "food" | "machinery"
  | "chemicals" | "furniture" | "medical" | "other";

export type ProductStatus = "active" | "discontinued" | "pending" | "out_of_stock";

export interface Product {
  id: number;
  sku: string;
  name: string;
  description?: string;
  category: ProductCategory;
  sub_category?: string;
  brand?: string;
  barcode?: string;
  unit_cost: number;
  unit_price: number;
  currency: string;
  weight_kg?: number;
  total_quantity: number;
  min_stock_level: number;
  max_stock_level: number;
  avg_daily_demand: number;
  turnover_rate: number;
  supplier_id?: number;
  status: ProductStatus;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

// ── Warehouse ─────────────────────────────────────────────────────────────────

export type WarehouseStatus = "active" | "maintenance" | "closed";

export interface Warehouse {
  id: number;
  name: string;
  code: string;
  address: string;
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  capacity_sqft: number;
  max_weight_kg?: number;
  current_utilization_pct: number;
  status: WarehouseStatus;
  manager_name?: string;
  manager_email?: string;
  is_active: boolean;
  created_at: string;
}

// ── Supplier ──────────────────────────────────────────────────────────────────

export type SupplierStatus = "active" | "inactive" | "blacklisted" | "probation";

export interface Supplier {
  id: number;
  name: string;
  code: string;
  contact_email: string;
  contact_phone?: string;
  address?: string;
  country?: string;
  status: SupplierStatus;
  on_time_delivery_rate: number;
  quality_score: number;
  price_competitiveness: number;
  lead_time_days: number;
  total_orders: number;
  composite_score: number;
  is_active: boolean;
  created_at: string;
}

// ── Order ─────────────────────────────────────────────────────────────────────

export type OrderType = "purchase" | "sales" | "transfer" | "return";
export type OrderStatus = "draft" | "pending" | "approved" | "processing" | "shipped" | "delivered" | "cancelled" | "returned";
export type OrderPriority = "low" | "medium" | "high" | "critical";

export interface OrderItem {
  id: number;
  product_id: number;
  quantity: number;
  quantity_received: number;
  unit_price: number;
  total_price: number;
}

export interface Order {
  id: number;
  order_number: string;
  order_type: OrderType;
  status: OrderStatus;
  priority: OrderPriority;
  supplier_id?: number;
  warehouse_id?: number;
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  total_amount: number;
  currency: string;
  expected_delivery?: string;
  delivered_at?: string;
  notes?: string;
  items: OrderItem[];
  created_at: string;
  updated_at?: string;
}

// ── Shipment ──────────────────────────────────────────────────────────────────

export type ShipmentStatus = "pending" | "picked_up" | "in_transit" | "out_for_delivery" | "delivered" | "delayed" | "failed" | "returned";
export type ShipmentCarrier = "fedex" | "ups" | "dhl" | "usps" | "internal" | "other";

export interface ShipmentEvent {
  id: number;
  status: ShipmentStatus;
  location?: string;
  description?: string;
  occurred_at: string;
}

export interface Shipment {
  id: number;
  tracking_number: string;
  order_id?: number;
  origin_warehouse_id?: number;
  dest_warehouse_id?: number;
  status: ShipmentStatus;
  carrier: ShipmentCarrier;
  route_distance_km?: number;
  estimated_cost?: number;
  weight_kg?: number;
  dispatched_at?: string;
  estimated_arrival?: string;
  actual_arrival?: string;
  delay_reason?: string;
  events: ShipmentEvent[];
  created_at: string;
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export interface DashboardKPIs {
  total_products: number;
  total_warehouses: number;
  total_suppliers: number;
  monthly_revenue: number;
  pending_orders: number;
  active_shipments: number;
  low_stock_alerts: number;
  avg_warehouse_utilization_pct: number;
  generated_at: string;
}

export interface ForecastResult {
  product_id: number;
  periods_ahead: number;
  forecast: number[];
  trend: number;
  rmse: number;
  mape: number;
  confidence_lower: number[];
  confidence_upper: number[];
}

export interface RestockItem {
  product_id: number;
  sku: string;
  name: string;
  warehouse_id: number;
  current_stock: number;
  reorder_point: number;
  days_until_stockout: number;
  urgency_score: number;
}

export interface SupplierRank {
  supplier_id: number;
  name: string;
  composite_score: number;
  rank: number;
  breakdown: {
    on_time_delivery: number;
    quality: number;
    price: number;
    lead_time: number;
  };
}
