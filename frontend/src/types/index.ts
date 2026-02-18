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

export interface MultiLayerCause extends AnalysisCause {
  impact_level?: "critical" | "significant" | "minor";
}

export interface OutlookItem {
  summary: string;
  sentiment: "bullish" | "bearish" | "neutral";
  catalysts: string[];
}

export interface AnalysisOutlook {
  short_term?: OutlookItem;
  medium_term?: OutlookItem;
}

export interface SectorRelatedStock {
  name: string;
  code: string;
  change_pct: number;
}

export interface SectorImpact {
  sector: string;
  related_stocks: SectorRelatedStock[];
  correlation_note: string;
}

export interface AnalysisResult {
  summary: string;
  causes: AnalysisCause[];
  direct_causes?: MultiLayerCause[];
  indirect_causes?: MultiLayerCause[];
  macro_factors?: MultiLayerCause[];
  outlook?: AnalysisOutlook;
  sector_impact?: SectorImpact;
}

export interface TrendPoint {
  day: number;
  change_pct: number;
}

export interface CaseAftermath {
  after_1w_pct: number | null;
  after_1m_pct: number | null;
  recovery_days: number | null;
}

export interface SimilarCaseItem {
  date: string;
  change_pct: number;
  volume: number;
  similarity_score: number;
  trend_1w: TrendPoint[];
  trend_1m: TrendPoint[];
  data_insufficient: boolean;
  aftermath?: CaseAftermath | null;
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

export interface NewsItem {
  id: number;
  stock_id: string | null;
  stock_name: string | null;
  title: string;
  url: string;
  source: string;
  summary: string | null;
  importance: string | null;
  published_at: string | null;
}

export interface NewsFeedResponse {
  items: NewsItem[];
  page: number;
  per_page: number;
  total: number;
  has_more: boolean;
  message: string | null;
}

export interface BriefingKeyIssue {
  title: string;
  description: string;
}

export interface BriefingTopMover {
  stock_name: string;
  change_pct: number;
  reason: string;
}

export interface BriefingResponse {
  id: number;
  market: string;
  date: string;
  summary: string | null;
  key_issues: BriefingKeyIssue[] | null;
  top_movers: BriefingTopMover[] | null;
  created_at: string | null;
}

export interface BriefingTodayResponse extends BriefingResponse {
  is_today: boolean;
}

export interface TrendingStock {
  stock_id: string;
  stock_name: string;
  stock_code: string;
  market: string;
  change_pct: number;
  event_count: number;
  latest_report_id: string | null;
  mini_summary: string | null;
}

export interface PopularStock {
  stock_id: string;
  stock_name: string;
  stock_code: string;
  market: string;
  tracking_count: number;
  latest_price: number | null;
  price_change_pct: number | null;
  latest_change_reason: string | null;
}

export interface CalendarEvent {
  id: number;
  event_type: string;
  title: string;
  description: string | null;
  event_date: string;
  market: string;
  stock_name: string | null;
  is_tracked: boolean;
}
