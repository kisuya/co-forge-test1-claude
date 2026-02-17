"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { briefingsApi } from "@/lib/queries";
import type { BriefingTodayResponse } from "@/types";
import Skeleton from "@/components/Skeleton";

export default function BriefingCard() {
  const [briefing, setBriefing] = useState<BriefingTodayResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeMarket, setActiveMarket] = useState<"KR" | "US">("KR");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    briefingsApi
      .getToday(activeMarket)
      .then((res) => {
        if (!cancelled) setBriefing(res.data);
      })
      .catch(() => {
        if (!cancelled) setBriefing(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeMarket]);

  // Don't show the card if no briefing data
  if (!loading && (!briefing || !briefing.summary)) {
    return null;
  }

  const formatDate = (dateStr: string) => {
    const parts = dateStr.split("-");
    if (parts.length === 3) return `${parts[0]}.${parts[1]}.${parts[2]}`;
    return dateStr;
  };

  return (
    <div
      className="bg-white rounded-lg border border-gray-200 p-6 mb-6"
      data-testid="briefing-card"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-lg" role="img" aria-label="chart">
            📈
          </span>
          <h3 className="text-lg font-semibold text-gray-900">오늘의 시장</h3>
          {briefing && (
            <span className="text-sm text-gray-500">
              {formatDate(briefing.date)}
            </span>
          )}
        </div>
        <div className="flex" role="tablist" aria-label="시장 선택">
          <button
            role="tab"
            aria-selected={activeMarket === "KR"}
            className={`px-3 py-1 text-sm rounded-l-md border ${
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
            className={`px-3 py-1 text-sm rounded-r-md border-t border-b border-r ${
              activeMarket === "US"
                ? "bg-blue-600 text-white border-blue-600"
                : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
            }`}
            onClick={() => setActiveMarket("US")}
          >
            미국
          </button>
        </div>
      </div>

      {loading ? (
        <div data-testid="briefing-skeleton">
          <Skeleton width="100%" height={40} className="mb-3" />
          <Skeleton width="80%" height={16} className="mb-2" />
          <Skeleton width="60%" height={16} className="mb-2" />
          <Skeleton width="70%" height={16} />
        </div>
      ) : briefing && briefing.summary ? (
        <>
          {/* Summary */}
          <p
            className="text-base text-gray-800 mb-4 line-clamp-2"
            data-testid="briefing-summary"
          >
            {briefing.summary}
          </p>

          {/* Key Issues */}
          {briefing.key_issues && briefing.key_issues.length > 0 && (
            <div className="mb-4" data-testid="briefing-issues">
              <h4 className="text-sm font-medium text-gray-600 mb-2">
                주요 이슈
              </h4>
              <ul className="space-y-1">
                {briefing.key_issues.slice(0, 3).map((issue, idx) => (
                  <li
                    key={idx}
                    className="text-sm text-gray-700 flex items-start gap-2"
                  >
                    <span className="text-gray-400 mt-0.5">•</span>
                    <span>{issue.title}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Top Movers */}
          {briefing.top_movers && briefing.top_movers.length > 0 && (
            <div className="mb-4" data-testid="briefing-movers">
              <h4 className="text-sm font-medium text-gray-600 mb-2">
                특징주
              </h4>
              <div className="flex flex-wrap gap-3">
                {briefing.top_movers.slice(0, 3).map((mover, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-1 text-sm"
                  >
                    <span className="font-medium text-gray-800">
                      {mover.stock_name}
                    </span>
                    <span
                      className={
                        mover.change_pct > 0
                          ? "text-red-600"
                          : mover.change_pct < 0
                          ? "text-blue-600"
                          : "text-gray-500"
                      }
                    >
                      {mover.change_pct > 0 ? "▲" : mover.change_pct < 0 ? "▼" : ""}
                      {mover.change_pct > 0 ? "+" : ""}
                      {mover.change_pct.toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Footer link */}
          <Link
            href="/briefings"
            className="text-sm text-blue-600 hover:underline"
            data-testid="briefing-link"
          >
            전체 보기
          </Link>
        </>
      ) : null}
    </div>
  );
}
