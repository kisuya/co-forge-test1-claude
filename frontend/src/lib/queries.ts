import api from "./api";
import type { Stock, WatchlistItem, Report } from "@/types";

export const stocksApi = {
  search: (q: string) =>
    api.get<Stock[]>("/api/stocks/search", { params: { q } }),
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
