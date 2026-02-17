"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { newsApi } from "@/lib/queries";
import type { NewsItem } from "@/types";

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

export default function NewsWidget() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    newsApi
      .list({ importance: "high", per_page: 5 })
      .then((res) => {
        if (!cancelled) setItems(res.data.items);
      })
      .catch(() => {
        if (!cancelled) setItems([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Don't show widget if no news
  if (!loading && items.length === 0) {
    return null;
  }

  if (loading) {
    return null;
  }

  return (
    <div
      className="bg-white rounded-lg border border-gray-200 p-6 mb-6"
      data-testid="news-widget"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          📰 관심 종목 뉴스
        </h3>
      </div>

      <div className="space-y-3" data-testid="news-widget-list">
        {items.map((item) => (
          <a
            key={item.id}
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-2 group"
            data-testid="news-widget-item"
          >
            {item.stock_name && (
              <span
                className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full shrink-0 mt-0.5"
                data-testid="news-widget-stock-tag"
              >
                {item.stock_name}
              </span>
            )}
            <div className="min-w-0 flex-1">
              <p className="text-sm text-gray-800 group-hover:text-blue-600 truncate">
                {item.summary || item.title}
              </p>
              <span className="text-xs text-gray-400">
                {relativeTime(item.published_at)}
              </span>
            </div>
          </a>
        ))}
      </div>

      <Link
        href="/news"
        className="block text-sm text-blue-600 hover:underline mt-4"
        data-testid="news-widget-link"
      >
        전체 뉴스 보기
      </Link>
    </div>
  );
}
