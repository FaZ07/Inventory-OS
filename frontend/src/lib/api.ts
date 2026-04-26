import axios, { AxiosError } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// Attach JWT on every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh`, { refresh_token: refresh });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${data.access_token}`;
            return axios(error.config);
          }
        } catch {
          localStorage.clear();
          window.location.href = "/auth/login";
        }
      } else {
        window.location.href = "/auth/login";
      }
    }
    return Promise.reject(error);
  }
);

// ── API helpers ───────────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  register: (data: object) => api.post("/auth/register", data),
  me: () => api.get("/auth/me"),
};

export const productsApi = {
  list: (params?: object) => api.get("/products", { params }),
  get: (id: number) => api.get(`/products/${id}`),
  create: (data: object) => api.post("/products", data),
  update: (id: number, data: object) => api.patch(`/products/${id}`, data),
  delete: (id: number) => api.delete(`/products/${id}`),
  search: (q: string, fuzzy?: boolean, top_k?: number) =>
    api.get("/products/search", { params: { q, fuzzy, top_k } }),
  eoq: (id: number, params: object) => api.get(`/products/${id}/eoq`, { params }),
  safetyStock: (id: number, params: object) => api.get(`/products/${id}/safety-stock`, { params }),
};

export const warehousesApi = {
  list: () => api.get("/warehouses"),
  get: (id: number) => api.get(`/warehouses/${id}`),
  create: (data: object) => api.post("/warehouses", data),
  update: (id: number, data: object) => api.patch(`/warehouses/${id}`, data),
  delete: (id: number) => api.delete(`/warehouses/${id}`),
  stock: (id: number) => api.get(`/warehouses/${id}/stock`),
  updateStock: (whId: number, prodId: number, data: object) =>
    api.put(`/warehouses/${whId}/stock/${prodId}`, data),
  optimizeRoute: (data: object) => api.post("/warehouses/route/optimize", data),
};

export const suppliersApi = {
  list: (params?: object) => api.get("/suppliers", { params }),
  get: (id: number) => api.get(`/suppliers/${id}`),
  create: (data: object) => api.post("/suppliers", data),
  update: (id: number, data: object) => api.patch(`/suppliers/${id}`, data),
  rankings: () => api.get("/suppliers/rankings"),
};

export const ordersApi = {
  list: (params?: object) => api.get("/orders", { params }),
  get: (id: number) => api.get(`/orders/${id}`),
  create: (data: object) => api.post("/orders", data),
  update: (id: number, data: object) => api.patch(`/orders/${id}`, data),
  cancel: (id: number) => api.post(`/orders/${id}/cancel`),
  priorityQueue: (top_k?: number) => api.get("/orders/priority-queue", { params: { top_k } }),
};

export const shipmentsApi = {
  list: (params?: object) => api.get("/shipments", { params }),
  get: (id: number) => api.get(`/shipments/${id}`),
  create: (data: object) => api.post("/shipments", data),
  update: (id: number, data: object) => api.patch(`/shipments/${id}`, data),
  delayRisk: () => api.get("/shipments/delay-risk"),
};

export const analyticsApi = {
  dashboard: () => api.get("/analytics/dashboard"),
  revenueTrend: (days?: number) => api.get("/analytics/revenue-trend", { params: { days } }),
  warehouseUtilization: () => api.get("/analytics/warehouse-utilization"),
  topProducts: (limit?: number) => api.get("/analytics/top-products", { params: { limit } }),
  restockQueue: () => api.get("/analytics/restock-queue"),
  supplierRankings: () => api.get("/analytics/supplier-rankings"),
  forecast: (productId: number, periods?: number) =>
    api.get(`/analytics/forecast/${productId}`, { params: { periods } }),
  supplyChainHealth: () => api.get("/analytics/supply-chain-health"),
  replenishmentPlan: (data: object) => api.post("/analytics/replenishment-plan", data),
};
