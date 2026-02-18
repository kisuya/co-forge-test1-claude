"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Report, OutlookItem, MultiLayerCause, AnalysisCause } from "@/types";
import AlertBadge from "./AlertBadge";
import SimilarCases from "./SimilarCases";

interface ReportViewProps {
  report: Report;
  shareMode?: boolean;
}

function confidenceLabel(c: string): string {
  switch (c) {
    case "high": return "높음";
    case "medium": return "중간";
    case "low": return "낮음";
    default: return c;
  }
}

function confidenceColor(c: string): string {
  switch (c) {
    case "high": return "bg-green-100 text-green-800";
    case "medium": return "bg-yellow-100 text-yellow-800";
    case "low": return "bg-gray-100 text-gray-600";
    default: return "bg-gray-100 text-gray-600";
  }
}

function impactLevelLabel(level: string): string {
  switch (level) {
    case "critical": return "심각";
    case "significant": return "중요";
    case "minor": return "경미";
    default: return level;
  }
}

function impactLevelColor(level: string): string {
  switch (level) {
    case "critical": return "bg-red-100 text-red-700";
    case "significant": return "bg-orange-100 text-orange-700";
    case "minor": return "bg-gray-100 text-gray-500";
    default: return "bg-gray-100 text-gray-500";
  }
}

function statusLabel(s: string): string {
  switch (s) {
    case "completed": return "완료";
    case "pending": return "대기중";
    case "generating": return "생성중";
    case "failed": return "실패";
    default: return s;
  }
}

function sentimentLabel(s: string): string {
  switch (s) {
    case "bullish": return "긍정적";
    case "bearish": return "부정적";
    case "neutral": return "중립";
    default: return s;
  }
}

function sentimentColor(s: string): string {
  switch (s) {
    case "bullish": return "bg-green-100 text-green-800";
    case "bearish": return "bg-red-100 text-red-800";
    case "neutral": return "bg-gray-100 text-gray-600";
    default: return "bg-gray-100 text-gray-600";
  }
}

type CauseTabKey = "direct" | "indirect" | "macro";

const CAUSE_TABS: { key: CauseTabKey; label: string }[] = [
  { key: "direct", label: "직접 원인" },
  { key: "indirect", label: "간접 원인" },
  { key: "macro", label: "시장 환경" },
];

function CauseCard({ cause }: { cause: MultiLayerCause }) {
  return (
    <div className="border border-gray-100 rounded-lg p-3" data-testid="cause-card">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm text-gray-800 font-medium">{cause.reason}</p>
        <div className="flex items-center gap-1.5 shrink-0">
          {cause.impact_level && (
            <span
              className={`px-2 py-0.5 text-xs rounded-full ${impactLevelColor(cause.impact_level)}`}
              data-testid="impact-level-badge"
            >
              {impactLevelLabel(cause.impact_level)}
            </span>
          )}
          <span
            className={`px-2 py-0.5 text-xs rounded-full ${confidenceColor(cause.confidence)}`}
          >
            {confidenceLabel(cause.confidence)}
          </span>
        </div>
      </div>
      {cause.impact && (
        <p className="text-xs text-gray-500 mt-1">{cause.impact}</p>
      )}
    </div>
  );
}

function FlatCauseCard({ cause }: { cause: AnalysisCause }) {
  return (
    <div className="border border-gray-100 rounded-lg p-3" data-testid="cause-card-flat">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm text-gray-800 font-medium">{cause.reason}</p>
        <span
          className={`shrink-0 px-2 py-0.5 text-xs rounded-full ${confidenceColor(cause.confidence)}`}
        >
          {confidenceLabel(cause.confidence)}
        </span>
      </div>
      {cause.impact && (
        <p className="text-xs text-gray-500 mt-1">{cause.impact}</p>
      )}
    </div>
  );
}

function MultiLayerCauses({ report }: { report: Report }) {
  const [activeTab, setActiveTab] = useState<CauseTabKey>("direct");
  const analysis = report.analysis;
  if (!analysis) return null;

  const tabData: Record<CauseTabKey, MultiLayerCause[]> = {
    direct: analysis.direct_causes ?? [],
    indirect: analysis.indirect_causes ?? [],
    macro: analysis.macro_factors ?? [],
  };

  const totalCount = tabData.direct.length + tabData.indirect.length + tabData.macro.length;
  if (totalCount === 0) return null;

  const activeCauses = tabData[activeTab];

  return (
    <div className="px-4 sm:px-6 py-4" data-testid="multilayer-causes">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">원인 분석</h3>
      <div className="flex border-b border-gray-200 mb-3" data-testid="cause-tabs">
        {CAUSE_TABS.map((tab) => {
          const count = tabData[tab.key].length;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
              data-testid={`cause-tab-${tab.key}`}
            >
              {tab.label}
              {count > 0 && (
                <span className="ml-1.5 text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>
      <div className="space-y-3" data-testid={`cause-panel-${activeTab}`}>
        {activeCauses.length > 0 ? (
          activeCauses.map((cause, i) => <CauseCard key={i} cause={cause} />)
        ) : (
          <p className="text-sm text-gray-400 py-2" data-testid="cause-panel-empty">
            해당 카테고리의 원인이 없습니다
          </p>
        )}
      </div>
    </div>
  );
}

function OutlookCard({ title, outlook }: { title: string; outlook: OutlookItem }) {
  return (
    <div className="border border-gray-100 rounded-lg p-3" data-testid={`outlook-${title === "단기 전망" ? "short" : "medium"}`}>
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-700">{title}</h4>
        <span className={`px-2 py-0.5 text-xs rounded-full ${sentimentColor(outlook.sentiment)}`}>
          {sentimentLabel(outlook.sentiment)}
        </span>
      </div>
      <p className="text-sm text-gray-800">{outlook.summary}</p>
      {outlook.catalysts && outlook.catalysts.length > 0 && (
        <ul className="mt-2 space-y-1">
          {outlook.catalysts.map((c, i) => (
            <li key={i} className="text-xs text-gray-500 flex items-start gap-1">
              <span className="text-gray-400 mt-0.5">&#8226;</span>
              <span>{c}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function hasMultiLayerCauses(report: Report): boolean {
  const a = report.analysis;
  if (!a) return false;
  return (
    (a.direct_causes && a.direct_causes.length > 0) ||
    (a.indirect_causes && a.indirect_causes.length > 0) ||
    (a.macro_factors && a.macro_factors.length > 0)
  ) === true;
}

export default function ReportView({ report, shareMode = false }: ReportViewProps) {
  const router = useRouter();
  const causes = report.analysis?.causes ?? [];
  const isMultiLayer = hasMultiLayerCauses(report);

  return (
    <article className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden" data-testid="report-view">
      <div className="p-4 sm:p-6 border-b border-gray-100">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h2 className="text-lg sm:text-xl font-bold text-gray-900">
              {shareMode ? (
                <span data-testid="report-stock-name">{report.stock_name}</span>
              ) : (
                <span
                  onClick={() => router.push(`/stocks/${report.stock_id}`)}
                  className="cursor-pointer hover:underline"
                  data-testid="report-stock-link"
                >
                  {report.stock_name}
                </span>
              )}
              <span className="ml-2 text-sm font-normal text-gray-500">
                {report.stock_code}
              </span>
            </h2>
            {report.created_at && (
              <p className="text-xs text-gray-400 mt-1">
                {new Date(report.created_at).toLocaleString("ko-KR")}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <AlertBadge changePct={report.trigger_change_pct} size="md" />
            <span className="text-xs text-gray-500">
              {statusLabel(report.status)}
            </span>
          </div>
        </div>
      </div>

      {report.summary && (
        <div className="px-4 sm:px-6 py-4 bg-gray-50">
          <h3 className="text-sm font-semibold text-gray-700 mb-1">요약</h3>
          <p className="text-gray-800">{report.summary}</p>
        </div>
      )}

      {isMultiLayer ? (
        <MultiLayerCauses report={report} />
      ) : causes.length > 0 ? (
        <div className="px-4 sm:px-6 py-4" data-testid="flat-causes">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">원인 분석</h3>
          <div className="space-y-3">
            {causes.map((cause, i) => (
              <FlatCauseCard key={i} cause={cause} />
            ))}
          </div>
        </div>
      ) : null}

      {(report.analysis?.outlook?.short_term || report.analysis?.outlook?.medium_term) && (
        <div className="px-4 sm:px-6 py-4 border-t border-gray-100" data-testid="outlook-section">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">전망</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {report.analysis.outlook.short_term && (
              <OutlookCard title="단기 전망" outlook={report.analysis.outlook.short_term} />
            )}
            {report.analysis.outlook.medium_term && (
              <OutlookCard title="중기 전망" outlook={report.analysis.outlook.medium_term} />
            )}
          </div>
        </div>
      )}

      {report.analysis?.sector_impact && report.analysis.sector_impact.related_stocks.length > 0 && (
        <div className="px-4 sm:px-6 py-4 border-t border-gray-100" data-testid="sector-impact-section">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">
            섹터 영향 <span className="text-xs font-normal text-gray-400 ml-1">{report.analysis.sector_impact.sector}</span>
          </h3>
          <p className="text-xs text-gray-500 mb-3">{report.analysis.sector_impact.correlation_note}</p>
          <div className="space-y-1.5">
            {report.analysis.sector_impact.related_stocks.map((rs, i) => (
              <div key={i} className="flex items-center justify-between text-sm" data-testid="sector-related-stock">
                <span className="text-gray-700">{rs.name} <span className="text-xs text-gray-400">{rs.code}</span></span>
                <span className={`font-medium ${rs.change_pct >= 0 ? "text-red-600" : "text-blue-600"}`}>
                  {rs.change_pct >= 0 ? "+" : ""}{rs.change_pct.toFixed(2)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {report.sources.length > 0 && (
        <div className="px-4 sm:px-6 py-4 border-t border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">출처</h3>
          <ul className="space-y-1">
            {report.sources.map((src) => (
              <li key={src.id} className="text-sm">
                <span className="text-xs text-gray-400 mr-1">
                  [{src.source_type}]
                </span>
                <a
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  {src.title}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!shareMode && (
        <div className="px-4 sm:px-6 py-4 border-t border-gray-100">
          <SimilarCases reportId={report.id} />
        </div>
      )}
    </article>
  );
}
