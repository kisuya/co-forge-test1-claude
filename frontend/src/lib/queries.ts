import api from "./api";
import type { Stock, WatchlistItem, Report, CasesResponse } from "@/types";

export const stocksApi = {
  search: (q: string, market?: string, signal?: AbortSignal) =>
    api.get<Stock[]>("/api/stocks/search", {
      params: { q, ...(market && { market }) },
      signal,
    }),
};

export const watchlistApi = {
  getAll: () => api.get<WatchlistItem[]>("/api/watchlist"),
  add: (stockId: string) =>
    api.post<WatchlistItem>("/api/watchlist", { stock_id: stockId }),
  remove: (itemId: string) => api.delete(`/api/watchlist/${itemId}`),
  updateThreshold: (itemId: string, threshold: number) =>
    api.patch<WatchlistItem>(`/api/watchlist/${itemId}`, { threshold }),
};

export const reportsApi = {
  getAll: () => api.get<Report[]>("/api/reports"),
  getById: (id: string) => api.get<Report>(`/api/reports/${id}`),
  getByStock: (stockId: string) =>
    api.get<Report[]>(`/api/reports/stock/${stockId}`),
};

export interface PushStatus {
  subscribed: boolean;
  endpoint_count: number;
}

export const casesApi = {
  getByReport: (reportId: string) =>
    api.get<CasesResponse>(`/api/cases/${reportId}`),
};

export const pushApi = {
  subscribe: (endpoint: string, p256dh: string, auth: string) =>
    api.post("/api/push/subscribe", { endpoint, p256dh, auth }),
  unsubscribe: (endpoint: string) =>
    api.delete("/api/push/unsubscribe", { data: { endpoint } }),
  status: () => api.get<PushStatus>("/api/push/status"),
};
