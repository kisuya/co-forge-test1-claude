"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { trendingApi } from "@/lib/queries";
import type { TrendingStock, PopularStock } from "@/types";
import Skeleton from "@/components/Skeleton";

export default function TrendingWidget() {
  const [activeTab, setActiveTab] = useState<"trending" | "popular">("trending");
  const [trendingItems, setTrendingItems] = useState<TrendingStock[]>([]);
  const [popularItems, setPopularItems] = useState<PopularStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);

    const fetchData = async () => {
      try {
        const [trendRes, popRes] = await Promise.all([
          trendingApi.getTrending(),
          trendingApi.getPopular(),
        ]);
        if (!cancelled) {
          setTrendingItems(trendRes.data);
          setPopularItems(popRes.data);
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
  }, []);

  // Hide widget on error
  if (error) return null;

  // Hide widget if no data at all
  if (!loading && trendingItems.length === 0 && popularItems.length === 0) {
    return null;
  }

  const items = activeTab === "trending" ? trendingItems : popularItems;

  return (
    <div
      className="bg-white rounded-lg border border-gray-200 p-4 mb-6 md:p-6"
      data-testid="trending-widget"
    >
      {/* Tab headers */}
      <div className="flex items-center gap-4 mb-4" role="tablist" aria-label="트렌딩 탭">
        <button
          role="tab"
          aria-selected={activeTab === "trending"}
          className={`text-sm font-semibold pb-1 border-b-2 ${
            activeTab === "trending"
              ? "text-gray-900 border-blue-600"
              : "text-gray-400 border-transparent hover:text-gray-600"
          }`}
          onClick={() => setActiveTab("trending")}
          data-testid="tab-trending"
        >
          🔥 트렌딩
        </button>
        <button
          role="tab"
          aria-selected={activeTab === "popular"}
          className={`text-sm font-semibold pb-1 border-b-2 ${
            activeTab === "popular"
              ? "text-gray-900 border-blue-600"
              : "text-gray-400 border-transparent hover:text-gray-600"
          }`}
          onClick={() => setActiveTab("popular")}
          data-testid="tab-popular"
        >
          ⭐ 인기
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div data-testid="trending-skeleton">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-2 py-2">
              <Skeleton width="120px" height={16} />
              <Skeleton width="60px" height={16} />
            </div>
          ))}
        </div>
      ) : (
        <>
          {/* Desktop: vertical list; Mobile: horizontal scroll */}
          <div
            className="md:space-y-2 flex md:flex-col gap-3 md:gap-0 overflow-x-auto md:overflow-visible pb-2 md:pb-0"
            data-testid="trending-list"
          >
            {items.slice(0, 10).map((item) => (
              <Link
                key={item.stock_id}
                href={`/stocks/${item.stock_id}`}
                className="flex-shrink-0 md:flex-shrink md:w-auto flex items-center gap-2 py-2 px-3 md:px-0 rounded-lg md:rounded-none bg-gray-50 md:bg-transparent hover:bg-gray-100 md:hover:bg-gray-50 transition-colors"
                data-testid="trending-item"
              >
                <span className="text-sm font-medium text-gray-800 whitespace-nowrap">
                  {item.stock_name}
                </span>
                {activeTab === "trending" && "change_pct" in item && (
                  <>
                    <span
                      className={`text-sm ${
                        (item as TrendingStock).change_pct > 0
                          ? "text-red-600"
                          : "text-blue-600"
                      }`}
                      data-testid="trending-change"
                    >
                      {(item as TrendingStock).change_pct > 0 ? "+" : ""}
                      {(item as TrendingStock).change_pct.toFixed(1)}%
                    </span>
                    <span className="text-xs text-gray-400" data-testid="trending-event-count">
                      📊 {(item as TrendingStock).event_count}건
                    </span>
                  </>
                )}
                {activeTab === "popular" && "tracking_count" in item && (
                  <>
                    <span className="text-xs text-gray-500" data-testid="popular-tracking-count">
                      👥 {(item as PopularStock).tracking_count}명
                    </span>
                    {(item as PopularStock).latest_price != null && (
                      <span className="text-sm text-gray-600" data-testid="popular-price">
                        {(item as PopularStock).latest_price?.toLocaleString()}
                      </span>
                    )}
                  </>
                )}
              </Link>
            ))}
          </div>

          {/* No data message */}
          {items.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-4" data-testid="trending-empty">
              데이터가 없습니다
            </p>
          )}
        </>
      )}
    </div>
  );
}
