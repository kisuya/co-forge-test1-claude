"use client";

import { useRouter } from "next/navigation";
import type { Report } from "@/types";
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

function statusLabel(s: string): string {
  switch (s) {
    case "completed": return "완료";
    case "pending": return "대기중";
    case "generating": return "생성중";
    case "failed": return "실패";
    default: return s;
  }
}

export default function ReportView({ report, shareMode = false }: ReportViewProps) {
  const router = useRouter();
  const causes = report.analysis?.causes ?? [];

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

      {causes.length > 0 && (
        <div className="px-4 sm:px-6 py-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">원인 분석</h3>
          <div className="space-y-3">
            {causes.map((cause, i) => (
              <div
                key={i}
                className="border border-gray-100 rounded-lg p-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm text-gray-800 font-medium">
                    {cause.reason}
                  </p>
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
