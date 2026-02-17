"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { isLoggedIn } from "@/lib/auth";
import { trendingApi } from "@/lib/queries";
import type { TrendingStock, PopularStock } from "@/types";
import Skeleton from "@/components/Skeleton";

export default function TrendingPage() {
  const [trending, setTrending] = useState<TrendingStock[]>([]);
  const [popular, setPopular] = useState<PopularStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [marketFilter, setMarketFilter] = useState<"ALL" | "KR" | "US">("ALL");
  const [periodFilter, setPeriodFilter] = useState<"daily" | "weekly">("daily");

  useEffect(() => {
    document.title = "트렌딩 종목 | oh-my-stock";
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);

    const fetchData = async () => {
      try {
        const [trendRes, popRes] = await Promise.all([
          trendingApi.getTrending(marketFilter, periodFilter),
          trendingApi.getPopular(marketFilter),
        ]);
        if (!cancelled) {
          setTrending(trendRes.data);
          setPopular(popRes.data);
        }
      } catch {
        if (!cancelled) setError(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchData();
    return () => {
      cancelled = true;
    };
  }, [marketFilter, periodFilter]);

  const loggedIn = typeof window !== "undefined" && isLoggedIn();

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1
            className="text-2xl font-bold text-gray-900"
            data-testid="trending-page-title"
          >
            🔥 트렌딩 종목
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            급변동 및 인기 종목을 확인하세요
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 mb-6" data-testid="trending-filters">
          {/* Market tabs */}
          <div className="flex" role="tablist" aria-label="시장 선택">
            {(["ALL", "KR", "US"] as const).map((m) => (
              <button
                key={m}
                role="tab"
                aria-selected={marketFilter === m}
                className={`px-3 py-1.5 text-sm border ${
                  m === "ALL" ? "rounded-l-md" : m === "US" ? "rounded-r-md border-l-0" : "border-l-0"
                } ${
                  marketFilter === m
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
                }`}
                onClick={() => setMarketFilter(m)}
                data-testid={`filter-market-${m.toLowerCase()}`}
              >
                {m === "ALL" ? "전체" : m === "KR" ? "한국" : "미국"}
              </button>
            ))}
          </div>

          {/* Period toggle */}
          <div className="flex" role="tablist" aria-label="기간 선택">
            <button
              role="tab"
              aria-selected={periodFilter === "daily"}
              className={`px-3 py-1.5 text-sm rounded-l-md border ${
                periodFilter === "daily"
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
              }`}
              onClick={() => setPeriodFilter("daily")}
              data-testid="filter-period-daily"
            >
              일간
            </button>
            <button
              role="tab"
              aria-selected={periodFilter === "weekly"}
              className={`px-3 py-1.5 text-sm rounded-r-md border-t border-b border-r ${
                periodFilter === "weekly"
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
              }`}
              onClick={() => setPeriodFilter("weekly")}
              data-testid="filter-period-weekly"
            >
              주간
            </button>
          </div>
        </div>

        {/* Error state */}
        {error && (
          <div className="text-center py-16" data-testid="trending-error">
            <p className="text-lg text-gray-600">데이터를 불러올 수 없습니다</p>
            <button
              onClick={() => {
                setError(false);
                setLoading(true);
                trendingApi
                  .getTrending(marketFilter, periodFilter)
                  .then((res) => setTrending(res.data))
                  .catch(() => setError(true))
                  .finally(() => setLoading(false));
              }}
              className="mt-3 px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
              data-testid="trending-retry"
            >
              다시 시도
            </button>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="space-y-6" data-testid="trending-page-skeleton">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <Skeleton width="200px" height={24} className="mb-4" />
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-3 py-3">
                  <Skeleton width="24px" height={24} />
                  <Skeleton width="120px" height={18} />
                  <Skeleton width="80px" height={18} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Content */}
        {!loading && !error && (
          <div className="space-y-8">
            {/* Trending section */}
            <section data-testid="trending-section">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                🔥 급변동 종목
              </h2>
              {trending.length === 0 ? (
                <p
                  className="text-sm text-gray-400 py-8 text-center"
                  data-testid="trending-no-data"
                >
                  아직 트렌딩 데이터가 없습니다
                </p>
              ) : (
                <div className="space-y-3" data-testid="trending-page-list">
                  {trending.map((item) => (
                    <Link
                      key={item.stock_id}
                      href={`/stocks/${item.stock_id}`}
                      className="flex items-center gap-4 bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
                      data-testid="trending-page-item"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-base font-medium text-gray-900">
                            {item.stock_name}
                          </span>
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full ${
                              item.market === "KRX"
                                ? "bg-blue-50 text-blue-700"
                                : item.market === "NYSE"
                                ? "bg-green-50 text-green-700"
                                : "bg-purple-50 text-purple-700"
                            }`}
                            data-testid="trending-market-badge"
                          >
                            {item.market}
                          </span>
                        </div>
                        {item.mini_summary && (
                          <p className="text-sm text-gray-500 mt-1 truncate">
                            {item.mini_summary}
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        <span
                          className={`text-lg font-bold ${
                            item.change_pct > 0 ? "text-red-600" : "text-blue-600"
                          }`}
                        >
                          {item.change_pct > 0 ? "+" : ""}
                          {item.change_pct.toFixed(1)}%
                        </span>
                        {item.latest_report_id && (
                          <p className="text-xs text-gray-400 mt-1">리포트 보기</p>
                        )}
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </section>

            {/* Popular section */}
            <section data-testid="popular-section">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                ⭐ 인기 종목
              </h2>
              {popular.length === 0 ? (
                <p className="text-sm text-gray-400 py-8 text-center">
                  인기 종목 데이터가 없습니다
                </p>
              ) : (
                <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100" data-testid="popular-page-list">
                  {popular.map((item, idx) => (
                    <Link
                      key={item.stock_id}
                      href={`/stocks/${item.stock_id}`}
                      className="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors"
                      data-testid="popular-page-item"
                    >
                      <span className="text-lg font-bold text-gray-300 w-8 text-center" data-testid="popular-rank">
                        {idx + 1}
                      </span>
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-medium text-gray-900">
                          {item.stock_name}
                        </span>
                        <span className="text-xs text-gray-400 ml-2">
                          👥 {item.tracking_count}명
                        </span>
                      </div>
                      {item.latest_price != null && (
                        <span className="text-sm text-gray-600">
                          {item.latest_price.toLocaleString()}
                        </span>
                      )}
                    </Link>
                  ))}
                </div>
              )}
            </section>

            {/* CTA for non-logged-in users */}
            {!loggedIn && (
              <div
                className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center"
                data-testid="trending-cta"
              >
                <p className="text-base text-gray-800 mb-3">
                  종목을 추적하려면 가입하세요
                </p>
                <Link
                  href="/signup"
                  className="inline-block px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                >
                  무료로 시작하기
                </Link>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
