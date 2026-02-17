"use client";

import { useEffect, useState } from "react";
import { briefingsApi } from "@/lib/queries";
import type { BriefingResponse } from "@/types";
import Skeleton from "@/components/Skeleton";

export default function BriefingsArchivePage() {
  const [briefings, setBriefings] = useState<BriefingResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeMarket, setActiveMarket] = useState<"KR" | "US">("KR");
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    document.title = "마켓 브리핑 | oh-my-stock";
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    briefingsApi
      .list(activeMarket, 30)
      .then((res) => {
        if (!cancelled) setBriefings(res.data);
      })
      .catch(() => {
        if (!cancelled) setBriefings([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeMarket]);

  const formatDate = (dateStr: string) => {
    const parts = dateStr.split("-");
    if (parts.length === 3) {
      const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
      const days = ["일", "월", "화", "수", "목", "금", "토"];
      return `${parts[0]}.${parts[1]}.${parts[2]} (${days[d.getDay()]})`;
    }
    return dateStr;
  };

  const toggleExpand = (id: number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1
            className="text-2xl font-bold text-gray-900"
            data-testid="briefing-archive-title"
          >
            마켓 브리핑
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            매일 장 마감 후 AI가 생성하는 시장 요약
          </p>
        </div>

        {/* Market tabs */}
        <div className="flex mb-6" role="tablist" aria-label="시장 선택">
          <button
            role="tab"
            aria-selected={activeMarket === "KR"}
            data-testid="tab-kr"
            className={`px-4 py-2 text-sm font-medium rounded-l-md border ${
              activeMarket === "KR"
                ? "bg-blue-600 text-white border-blue-600"
                : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
            }`}
            onClick={() => setActiveMarket("KR")}
          >
            한국
          </button>
          <button
            role="tab"
            aria-selected={activeMarket === "US"}
            data-testid="tab-us"
            className={`px-4 py-2 text-sm font-medium rounded-r-md border-t border-b border-r ${
              activeMarket === "US"
                ? "bg-blue-600 text-white border-blue-600"
                : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
            }`}
            onClick={() => setActiveMarket("US")}
          >
            미국
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="space-y-4" data-testid="briefing-archive-skeleton">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="bg-white rounded-lg border border-gray-200 p-6"
              >
                <Skeleton width="200px" height={20} className="mb-3" />
                <Skeleton width="100%" height={40} className="mb-2" />
                <Skeleton width="80%" height={16} />
              </div>
            ))}
          </div>
        ) : briefings.length === 0 ? (
          <div
            className="text-center py-16 text-gray-500"
            data-testid="briefing-archive-empty"
          >
            <p className="text-lg">브리핑 데이터가 없습니다</p>
            <p className="text-sm mt-1">
              장 마감 후 자동으로 생성됩니다
            </p>
          </div>
        ) : (
          <div className="space-y-4" data-testid="briefing-archive-list">
            {briefings.map((briefing) => (
              <div
                key={briefing.id}
                className="bg-white rounded-lg border border-gray-200 p-6"
                data-testid="briefing-archive-item"
              >
                {/* Date header */}
                <div className="flex items-center justify-between mb-3">
                  <h3
                    className="text-base font-semibold text-gray-900"
                    data-testid="briefing-date"
                  >
                    {formatDate(briefing.date)}
                  </h3>
                  <span className="text-xs text-gray-400">
                    {briefing.market === "KR" ? "한국" : "미국"}
                  </span>
                </div>

                {/* Summary */}
                {briefing.summary && (
                  <p
                    className="text-sm text-gray-700 mb-3"
                    data-testid="briefing-archive-summary"
                  >
                    {briefing.summary}
                  </p>
                )}

                {/* Collapsible key issues */}
                {briefing.key_issues && briefing.key_issues.length > 0 && (
                  <div data-testid="briefing-archive-issues">
                    <button
                      onClick={() => toggleExpand(briefing.id)}
                      className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                      aria-expanded={expandedIds.has(briefing.id)}
                      data-testid="briefing-toggle-issues"
                    >
                      <span>
                        {expandedIds.has(briefing.id) ? "▾" : "▸"} 주요 이슈 (
                        {briefing.key_issues.length})
                      </span>
                    </button>
                    {expandedIds.has(briefing.id) && (
                      <ul className="mt-2 space-y-1 pl-4">
                        {briefing.key_issues.map((issue, idx) => (
                          <li
                            key={idx}
                            className="text-sm text-gray-600"
                          >
                            <span className="font-medium text-gray-800">
                              {issue.title}
                            </span>
                            {issue.description && (
                              <span className="text-gray-500">
                                {" "}
                                — {issue.description}
                              </span>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {/* Top movers */}
                {briefing.top_movers && briefing.top_movers.length > 0 && (
                  <div
                    className="mt-3 flex flex-wrap gap-3"
                    data-testid="briefing-archive-movers"
                  >
                    {briefing.top_movers.slice(0, 5).map((mover, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 text-sm"
                      >
                        <span className="text-gray-700">{mover.stock_name}</span>
                        <span
                          className={
                            mover.change_pct > 0
                              ? "text-red-600"
                              : mover.change_pct < 0
                              ? "text-blue-600"
                              : "text-gray-500"
                          }
                        >
                          {mover.change_pct > 0 ? "+" : ""}
                          {mover.change_pct.toFixed(1)}%
                        </span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
