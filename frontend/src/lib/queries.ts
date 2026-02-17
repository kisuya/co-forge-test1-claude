import api from "./api";
import type { Stock, WatchlistItem, Report, CasesResponse, StockDetail, StockHistoryResponse, ShareResponse, SharedReportResponse, ProfileResponse, ProfileReportItem, ProfileDiscussionItem, PaginatedResponse, DiscussionListResponse, DiscussionItem, CommentItem } from "@/types";

export const stocksApi = {
  search: (q: string, market?: string, signal?: AbortSignal) =>
    api.get<Stock[]>("/api/stocks/search", {
      params: { q, ...(market && { market }) },
      signal,
    }),
  getDetail: (stockId: string) =>
    api.get<StockDetail>(`/api/stocks/${stockId}`),
  getHistory: (stockId: string, page: number = 1, perPage: number = 20) =>
    api.get<StockHistoryResponse>(`/api/stocks/${stockId}/history`, {
      params: { page, per_page: perPage },
    }),
};

export const watchlistApi = {
  getAll: () => api.get<WatchlistItem[]>("/api/watchlist"),
  add: (stockId: string) =>
    api.post<WatchlistItem>("/api/watchlist", { stock_id: stockId }),
  remove: (itemId: string) => api.delete(`/api/watchlist/${itemId}`),
  updateThreshold: (itemId: string, threshold: number) =>
    api.patch<WatchlistItem>(`/api/watchlist/${itemId}`, { threshold }),
  updateAlert: (itemId: string, alert_enabled: boolean) =>
    api.patch<WatchlistItem>(`/api/watchlist/${itemId}`, { alert_enabled }),
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

export const shareApi = {
  create: (reportId: string) =>
    api.post<ShareResponse>(`/api/reports/${reportId}/share`),
  getShared: (token: string) =>
    api.get<SharedReportResponse>(`/api/shared/${token}`),
};

export const discussionsApi = {
  list: (stockId: string, page: number = 1, perPage: number = 20) =>
    api.get<DiscussionListResponse>(`/api/stocks/${stockId}/discussions`, {
      params: { page, per_page: perPage },
    }),
  create: (stockId: string, content: string) =>
    api.post<DiscussionItem>(`/api/stocks/${stockId}/discussions`, { content }),
  update: (discussionId: string, content: string) =>
    api.put<DiscussionItem>(`/api/discussions/${discussionId}`, { content }),
  delete: (discussionId: string) =>
    api.delete(`/api/discussions/${discussionId}`),
  listComments: (discussionId: string) =>
    api.get<CommentItem[]>(`/api/discussions/${discussionId}/comments`),
  createComment: (discussionId: string, content: string) =>
    api.post<CommentItem>(`/api/discussions/${discussionId}/comments`, { content }),
  deleteComment: (commentId: string) =>
    api.delete(`/api/comments/${commentId}`),
};

export const profileApi = {
  get: () => api.get<ProfileResponse>("/api/profile"),
  updateNickname: (nickname: string | null) =>
    api.put<ProfileResponse>("/api/profile", { nickname }),
  changePassword: (currentPassword: string, newPassword: string) =>
    api.put("/api/profile/password", {
      current_password: currentPassword,
      new_password: newPassword,
    }),
  getReports: (page: number = 1, perPage: number = 10) =>
    api.get<PaginatedResponse<ProfileReportItem>>("/api/profile/reports", {
      params: { page, per_page: perPage },
    }),
  getDiscussions: (page: number = 1, perPage: number = 10) =>
    api.get<PaginatedResponse<ProfileDiscussionItem>>("/api/profile/discussions", {
      params: { page, per_page: perPage },
    }),
};
