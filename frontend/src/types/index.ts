export interface Stock {
  id: string;
  code: string;
  name: string;
  name_kr: string | null;
  market: string;
  sector: string | null;
}

export interface WatchlistItem {
  id: string;
  stock_id: string;
  stock_code: string;
  stock_name: string;
  stock_market: string;
  threshold: number;
  alert_enabled: boolean;
  latest_price: number | null;
  price_change: number | null;
  price_change_pct: number | null;
  price_currency: string | null;
  price_updated_at: string | null;
  is_price_available: boolean;
  price_freshness: string;
  tracking_count: number;
}

export interface ReportSource {
  id: string;
  source_type: string;
  title: string;
  url: string;
}

export interface Report {
  id: string;
  stock_id: string;
  stock_code: string;
  stock_name: string;
  trigger_change_pct: number;
  summary: string | null;
  analysis: AnalysisResult | null;
  status: string;
  sources: ReportSource[];
  created_at: string | null;
  completed_at: string | null;
}

export interface AnalysisCause {
  reason: string;
  confidence: "high" | "medium" | "low";
  impact: string;
}

export interface AnalysisResult {
  summary: string;
  causes: AnalysisCause[];
}

export interface TrendPoint {
  day: number;
  change_pct: number;
}

export interface SimilarCaseItem {
  date: string;
  change_pct: number;
  volume: number;
  similarity_score: number;
  trend_1w: TrendPoint[];
  trend_1m: TrendPoint[];
  data_insufficient: boolean;
}

export interface CasesResponse {
  cases: SimilarCaseItem[];
  message?: string;
}

export interface ShareResponse {
  share_token: string;
  share_url: string;
  expires_at: string;
}

export interface SharedReportResponse {
  stock_name: string;
  stock_code: string;
  market: string;
  report: {
    summary: string | null;
    causes: Array<{ reason?: string; description?: string; confidence?: string; impact?: string }>;
    sources: Array<{ source_type: string; title: string; url: string }>;
    similar_cases: unknown[];
    created_at: string | null;
  };
  shared_at: string;
  expires_at: string;
}

export interface StockDetail {
  id: string;
  name: string;
  code: string;
  market: string;
  latest_price: number | null;
  price_change_pct: number | null;
  price_currency: string | null;
  price_freshness: string;
  tracking_count: number;
  tracking_since: string | null;
  is_tracked_by_me: boolean;
}

export interface HistoryEvent {
  id: string;
  date: string;
  change_pct: number;
  direction: "up" | "down";
  summary: string | null;
  confidence: "high" | "medium" | "low" | null;
  report_id: string;
}

export interface HistoryPagination {
  page: number;
  per_page: number;
  total: number;
  has_more: boolean;
}

export interface StockHistoryResponse {
  stock_id: string;
  stock_name: string;
  stock_code: string;
  market: string;
  tracking_since: string | null;
  events: HistoryEvent[];
  pagination: HistoryPagination;
  message: string | null;
}

export interface ProfileStats {
  watchlist_count: number;
  report_count: number;
  discussion_count: number;
}

export interface ProfileResponse {
  email: string;
  nickname: string | null;
  display_name: string;
  created_at: string;
  stats: ProfileStats | null;
}

export interface ProfileReportItem {
  id: string;
  stock_id: string;
  stock_name: string;
  change_pct: number;
  created_at: string;
}

export interface ProfileDiscussionItem {
  id: string;
  stock_id: string;
  stock_name: string;
  content: string;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  per_page: number;
  total: number;
  has_more: boolean;
}

export interface DiscussionItem {
  id: string;
  content: string;
  author_name: string;
  comment_count: number;
  created_at: string;
  updated_at: string | null;
  is_mine: boolean;
}

export interface DiscussionPagination {
  page: number;
  per_page: number;
  total: number;
  has_more: boolean;
}

export interface DiscussionListResponse {
  discussions: DiscussionItem[];
  pagination: DiscussionPagination;
}

export interface CommentItem {
  id: string;
  content: string;
  author_name: string;
  created_at: string;
  is_mine: boolean;
}
