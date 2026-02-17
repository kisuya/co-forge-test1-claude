"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { stocksApi } from "@/lib/queries";
import type { StockHistoryResponse, HistoryEvent } from "@/types";

interface EventTimelineProps {
  history: StockHistoryResponse;
  stockId: string;
}

const CONFIDENCE_BADGE: Record<string, string> = {
  high: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-gray-100 text-gray-500",
};

const CONFIDENCE_LABEL: Record<string, string> = {
  high: "높음",
  medium: "중간",
  low: "낮음",
};

function formatDate(dateStr: string): string {
  return dateStr.replace(/-/g, ".");
}

export default function EventTimeline({ history, stockId }: EventTimelineProps) {
  const router = useRouter();
  const [events, setEvents] = useState<HistoryEvent[]>(history.events);
  const [page, setPage] = useState(history.pagination.page);
  const [hasMore, setHasMore] = useState(history.pagination.has_more);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");

  const handleLoadMore = async () => {
    setLoadingMore(true);
    setError("");
    try {
      const nextPage = page + 1;
      const resp = await stocksApi.getHistory(stockId, nextPage);
      setEvents((prev) => [...prev, ...resp.data.events]);
      setPage(nextPage);
      setHasMore(resp.data.pagination.has_more);
    } catch {
      setError("이벤트를 불러올 수 없습니다. 다시 시도해주세요");
    } finally {
      setLoadingMore(false);
    }
  };

  const handleRetry = async () => {
    setError("");
    setLoadingMore(true);
    try {
      const resp = await stocksApi.getHistory(stockId, 1);
      setEvents(resp.data.events);
      setPage(1);
      setHasMore(resp.data.pagination.has_more);
    } catch {
      setError("이벤트를 불러올 수 없습니다. 다시 시도해주세요");
    } finally {
      setLoadingMore(false);
    }
  };

  // Error state (initial load failure)
  if (error && events.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6" data-testid="timeline-section">
        <h3 className="text-lg font-semibold text-gray-900 mb-4" data-testid="timeline-title">
          📈 이벤트 히스토리
        </h3>
        <div className="text-center py-8" data-testid="timeline-error">
          <p className="text-sm text-gray-600 mb-3">{error}</p>
          <button
            onClick={handleRetry}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
            data-testid="retry-button"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  // Empty state
  if (events.length === 0 && !error) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6" data-testid="timeline-section">
        <h3 className="text-lg font-semibold text-gray-900 mb-4" data-testid="timeline-title">
          📈 이벤트 히스토리
        </h3>
        {history.tracking_since && (
          <p className="text-xs text-gray-400 mb-4" data-testid="tracking-since">
            {formatDate(history.tracking_since.split("T")[0].split(" ")[0])}부터 추적 중
          </p>
        )}
        <div className="text-center py-12" data-testid="timeline-empty">
          <p className="text-4xl mb-4">🕐</p>
          <p className="text-lg text-gray-700 mb-2" data-testid="empty-title">
            아직 추적 이벤트가 없습니다
          </p>
          <p className="text-sm text-gray-500" data-testid="empty-description">
            급변동이 감지되면 자동으로 기록됩니다
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6" data-testid="timeline-section">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900" data-testid="timeline-title">
          📈 이벤트 히스토리
        </h3>
        {history.tracking_since && (
          <p className="text-xs text-gray-400 mt-1" data-testid="tracking-since">
            {formatDate(history.tracking_since.split("T")[0].split(" ")[0])}부터 추적 중
          </p>
        )}
      </div>

      <div className="relative" data-testid="timeline-list">
        {/* Timeline vertical line */}
        <div className="absolute left-4 top-0 bottom-0 w-px border-l-2 border-dashed border-gray-200" data-testid="timeline-line" />

        {events.map((event) => (
          <div
            key={event.id}
            className="relative pl-10 pb-6 cursor-pointer group"
            onClick={() => router.push(`/reports/${event.report_id}`)}
            data-testid="timeline-event"
          >
            {/* Timeline dot */}
            <div className={`absolute left-2.5 top-1 w-3 h-3 rounded-full border-2 ${
              event.direction === "up" ? "border-red-400 bg-red-50" : "border-blue-400 bg-blue-50"
            }`} />

            <div className="bg-white border border-gray-100 rounded-lg p-4 hover:shadow-md transition-shadow group-hover:-translate-y-0.5 transition-transform" data-testid="event-card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-500" data-testid="event-date">
                  {formatDate(event.date)}
                </span>
                <span
                  className={`text-xl font-bold ${event.direction === "up" ? "text-red-500" : "text-blue-500"}`}
                  data-testid="event-change"
                >
                  {event.direction === "up" ? "▲" : "▼"} {event.change_pct > 0 ? "+" : ""}{event.change_pct.toFixed(1)}%
                </span>
              </div>
              {event.summary && (
                <p className="text-sm text-gray-700 line-clamp-1" data-testid="event-summary">
                  {event.summary.length > 200 ? `${event.summary.slice(0, 200)}...` : event.summary}
                </p>
              )}
              {event.confidence && (
                <span
                  className={`inline-block mt-2 px-2 py-0.5 text-xs rounded-full font-medium ${CONFIDENCE_BADGE[event.confidence] || "bg-gray-100 text-gray-500"}`}
                  data-testid="event-confidence"
                >
                  {CONFIDENCE_LABEL[event.confidence] || event.confidence}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Load more button */}
      {hasMore && (
        <div className="text-center mt-4" data-testid="load-more-section">
          <button
            onClick={handleLoadMore}
            disabled={loadingMore}
            className="px-6 py-2 text-sm text-blue-600 hover:text-blue-700 border border-blue-200 rounded-lg hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="load-more-button"
          >
            {loadingMore ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />
                불러오는 중...
              </span>
            ) : (
              "이전 이벤트 더 보기"
            )}
          </button>
        </div>
      )}

      {/* Error during load more */}
      {error && events.length > 0 && (
        <div className="text-center mt-4" data-testid="load-more-error">
          <p className="text-sm text-red-500 mb-2">{error}</p>
          <button
            onClick={handleLoadMore}
            className="text-sm text-blue-600 hover:text-blue-700"
            data-testid="retry-button"
          >
            다시 시도
          </button>
        </div>
      )}
    </div>
  );
}
