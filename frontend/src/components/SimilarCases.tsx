"use client";

import { useState, useEffect } from "react";
import { casesApi } from "@/lib/queries";
import type { SimilarCaseItem } from "@/types";

interface SimilarCasesProps {
  reportId: string;
}

function changeColor(pct: number): string {
  return pct >= 0 ? "text-red-600" : "text-blue-600";
}

function formatPct(pct: number): string {
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

function similarityBadge(score: number): { label: string; cls: string } {
  if (score < 0.3) return { label: "높음", cls: "bg-green-100 text-green-800" };
  if (score < 0.7) return { label: "중간", cls: "bg-yellow-100 text-yellow-800" };
  return { label: "낮음", cls: "bg-gray-100 text-gray-600" };
}

function trendSummary(trend: { change_pct: number }[]): number | null {
  if (trend.length === 0) return null;
  return trend[trend.length - 1].change_pct;
}

export default function SimilarCases({ reportId }: SimilarCasesProps) {
  const [cases, setCases] = useState<SimilarCaseItem[]>([]);
  const [message, setMessage] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(true);

  useEffect(() => {
    casesApi
      .getByReport(reportId)
      .then((resp) => {
        setCases(resp.data.cases);
        setMessage(resp.data.message || "");
      })
      .catch(() => setMessage("유사 사례를 불러오지 못했습니다"))
      .finally(() => setLoading(false));
  }, [reportId]);

  if (loading) {
    return (
      <div className="mt-6 flex justify-center py-4">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <section className="mt-6" data-testid="similar-cases">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3"
        data-testid="similar-cases-toggle"
      >
        <span>{open ? "▼" : "▶"}</span>
        <span>과거 유사 사례</span>
      </button>
      {open && (
        <div data-testid="similar-cases-content">
          {cases.length === 0 ? (
            <div className="p-4 bg-gray-50 rounded-lg text-center" data-testid="similar-cases-empty">
              <p className="text-gray-500">
                이 종목의 유사한 과거 변동 사례가 아직 충분하지 않습니다
              </p>
              <p className="text-sm text-gray-400 mt-1">
                데이터가 쌓이면 자동으로 표시됩니다
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3" data-testid="similar-cases-list">
              {cases.map((c, i) => {
                const badge = similarityBadge(c.similarity_score);
                const w1 = trendSummary(c.trend_1w);
                const m1 = trendSummary(c.trend_1m);
                return (
                  <div
                    key={i}
                    className="border border-gray-200 rounded-lg p-4"
                    data-testid="similar-case-card"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-500">
                        {new Date(c.date).toLocaleDateString("ko-KR")}
                      </span>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${badge.cls}`}>
                        유사도: {badge.label}
                      </span>
                    </div>
                    <p className={`text-lg font-bold ${changeColor(c.change_pct)}`}>
                      {formatPct(c.change_pct)}
                    </p>
                    <div className="mt-2 flex gap-4 text-sm">
                      {w1 !== null && (
                        <span>
                          1주 후{" "}
                          <span className={changeColor(w1)}>{formatPct(w1)}</span>
                        </span>
                      )}
                      {m1 !== null && (
                        <span>
                          1개월 후{" "}
                          <span className={changeColor(m1)}>{formatPct(m1)}</span>
                        </span>
                      )}
                    </div>
                    {c.aftermath && (
                      <div className="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-600" data-testid="case-aftermath">
                        <span className="font-medium text-gray-500">이후 추이: </span>
                        {c.aftermath.after_1w_pct !== null && (
                          <span className="mr-3">
                            1주 후 <span className={changeColor(c.aftermath.after_1w_pct)}>{formatPct(c.aftermath.after_1w_pct)}</span>
                          </span>
                        )}
                        {c.aftermath.after_1m_pct !== null && (
                          <span className="mr-3">
                            1개월 후 <span className={changeColor(c.aftermath.after_1m_pct)}>{formatPct(c.aftermath.after_1m_pct)}</span>
                          </span>
                        )}
                        {c.aftermath.recovery_days !== null && (
                          <span className="text-gray-500">
                            회복까지 {c.aftermath.recovery_days}일 소요
                          </span>
                        )}
                      </div>
                    )}
                    {c.data_insufficient && !c.aftermath && (
                      <p className="text-xs text-gray-400 mt-1">
                        추이 데이터 부족
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
