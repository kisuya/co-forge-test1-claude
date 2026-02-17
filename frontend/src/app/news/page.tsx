"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { isLoggedIn } from "@/lib/auth";
import { newsApi, watchlistApi } from "@/lib/queries";
import type { NewsItem, WatchlistItem } from "@/types";
import Skeleton from "@/components/Skeleton";

function relativeTime(dateStr: string | null): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "방금 전";
  if (minutes < 60) return `${minutes}분 전`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  return `${days}일 전`;
}

function importanceBadge(importance: string | null) {
  if (!importance) return null;
  const styles: Record<string, string> = {
    high: "bg-red-100 text-red-700",
    medium: "bg-yellow-100 text-yellow-700",
    low: "bg-gray-100 text-gray-500",
  };
  const labels: Record<string, string> = {
    high: "높음",
    medium: "보통",
    low: "낮음",
  };
  return (
    <span
      className={`text-xs px-2 py-0.5 rounded-full ${styles[importance] || "bg-gray-100 text-gray-500"}`}
      data-testid="news-importance-badge"
    >
      {labels[importance] || importance}
    </span>
  );
}

export default function NewsFeedPage() {
  const router = useRouter();
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [page, setPage] = useState(1);
  const [stockFilter, setStockFilter] = useState<string>("");
  const [importanceFilter, setImportanceFilter] = useState<string>("");
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const observerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
    }
    document.title = "뉴스 피드 | oh-my-stock";
  }, [router]);

  // Load watchlist for filter dropdown
  useEffect(() => {
    watchlistApi.getAll().then((res) => setWatchlist(res.data)).catch(() => {});
  }, []);

  // Load news
  const fetchNews = useCallback(
    (pageNum: number, append: boolean = false) => {
      if (pageNum === 1) setLoading(true);
      else setLoadingMore(true);

      const params: Record<string, string | number> = { page: pageNum, per_page: 20 };
      if (stockFilter) params.stock_id = stockFilter;
      if (importanceFilter) params.importance = importanceFilter;

      newsApi
        .list(params)
        .then((res) => {
          if (append) {
            setItems((prev) => [...prev, ...res.data.items]);
          } else {
            setItems(res.data.items);
          }
          setHasMore(res.data.has_more);
        })
        .catch(() => {
          if (!append) setItems([]);
        })
        .finally(() => {
          setLoading(false);
          setLoadingMore(false);
        });
    },
    [stockFilter, importanceFilter]
  );

  useEffect(() => {
    setPage(1);
    fetchNews(1);
  }, [fetchNews]);

  // Intersection Observer for infinite scroll
  useEffect(() => {
    if (!observerRef.current) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore) {
          const nextPage = page + 1;
          setPage(nextPage);
          fetchNews(nextPage, true);
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(observerRef.current);
    return () => observer.disconnect();
  }, [hasMore, loadingMore, page, fetchNews]);

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1
            className="text-2xl font-bold text-gray-900"
            data-testid="news-feed-title"
          >
            📰 뉴스 피드
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            관심 종목의 최신 뉴스
          </p>
        </div>

        {/* Filters */}
        <div
          className="flex flex-wrap gap-3 mb-6"
          data-testid="news-filters"
        >
          <select
            value={stockFilter}
            onChange={(e) => setStockFilter(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
            data-testid="news-stock-filter"
            aria-label="종목 필터"
          >
            <option value="">전체 종목</option>
            {watchlist.map((item) => (
              <option key={item.stock_id} value={item.stock_id}>
                {item.stock_name}
              </option>
            ))}
          </select>
          <select
            value={importanceFilter}
            onChange={(e) => setImportanceFilter(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
            data-testid="news-importance-filter"
            aria-label="중요도 필터"
          >
            <option value="">전체 중요도</option>
            <option value="high">높음</option>
            <option value="medium">보통</option>
            <option value="low">낮음</option>
          </select>
        </div>

        {/* Content */}
        {loading ? (
          <div className="space-y-4" data-testid="news-skeleton">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="bg-white rounded-lg border border-gray-200 p-4"
              >
                <Skeleton width="60px" height={20} className="mb-2" />
                <Skeleton width="100%" height={18} className="mb-1" />
                <Skeleton width="80%" height={14} className="mb-2" />
                <Skeleton width="150px" height={12} />
              </div>
            ))}
          </div>
        ) : items.length === 0 ? (
          <div
            className="text-center py-16 text-gray-500"
            data-testid="news-empty"
          >
            <span className="text-4xl block mb-4">📰</span>
            <p className="text-lg">관심 종목의 뉴스가 없습니다</p>
            <p className="text-sm mt-1">종목을 추가해보세요</p>
          </div>
        ) : (
          <div className="space-y-3" data-testid="news-list">
            {items.map((item) => (
              <a
                key={item.id}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
                data-testid="news-item"
              >
                <div className="flex items-center gap-2 mb-2">
                  {item.stock_name && (
                    <span
                      className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full"
                      data-testid="news-stock-tag"
                    >
                      {item.stock_name}
                    </span>
                  )}
                  {importanceBadge(item.importance)}
                </div>
                {item.summary && (
                  <p
                    className="text-sm font-medium text-gray-900 mb-1"
                    data-testid="news-summary"
                  >
                    {item.summary}
                  </p>
                )}
                <p
                  className="text-xs text-gray-500 mb-2"
                  data-testid="news-title"
                >
                  {item.title}
                </p>
                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <span data-testid="news-source">{item.source}</span>
                  <span>·</span>
                  <span data-testid="news-time">
                    {relativeTime(item.published_at)}
                  </span>
                </div>
              </a>
            ))}

            {/* Infinite scroll sentinel */}
            <div ref={observerRef} data-testid="news-scroll-sentinel">
              {loadingMore && (
                <div className="text-center py-4" data-testid="news-loading-more">
                  <span className="text-sm text-gray-500">뉴스 불러오는 중...</span>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
