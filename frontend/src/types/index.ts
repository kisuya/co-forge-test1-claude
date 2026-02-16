export interface Stock {
  id: string;
  code: string;
  name: string;
  market: string;
  sector: string | null;
}

export interface WatchlistItem {
  id: string;
  stock_id: string;
  stock_code: string;
  stock_name: string;
  threshold: number;
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
