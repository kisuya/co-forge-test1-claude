"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { calendarApi } from "@/lib/queries";
import type { CalendarEvent } from "@/types";

const DAY_NAMES = ["일", "월", "화", "수", "목", "금", "토"];

const EVENT_TYPE_ICONS: Record<string, string> = {
  earnings: "📊",
  economic: "📈",
  central_bank: "🏦",
  dividend: "💰",
};

function formatEventDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  const month = d.getMonth() + 1;
  const day = d.getDate();
  const dayName = DAY_NAMES[d.getDay()];
  return `${month}/${day} (${dayName})`;
}

export default function CalendarWidget() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    calendarApi
      .getWeek()
      .then((res) => {
        if (!cancelled) setEvents(res.data);
      })
      .catch(() => {
        if (!cancelled) setEvents([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return null;
  }

  const sorted = [...events].sort(
    (a, b) => a.event_date.localeCompare(b.event_date)
  );
  const display = sorted.slice(0, 7);
  const hasMore = sorted.length > 7;

  // D-3 alerts: tracked earnings events within 3 days
  const todayMs = new Date().setHours(0, 0, 0, 0);
  const d3Alerts = events.filter((evt) => {
    if (!evt.is_tracked || evt.event_type !== "earnings") return false;
    const evtMs = new Date(evt.event_date + "T00:00:00").getTime();
    const diff = evtMs - todayMs;
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
    return days > 0 && days <= 3;
  });

  return (
    <div
      className="bg-white rounded-lg border border-gray-200 p-6 mb-6"
      data-testid="calendar-widget"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          📅 이번 주 주요 일정
        </h3>
      </div>

      {/* D-3 alerts */}
      {d3Alerts.length > 0 && (
        <div className="mb-4 space-y-2" data-testid="calendar-d3-alerts">
          {d3Alerts.map((evt) => (
            <div
              key={`d3-${evt.id}`}
              className="bg-yellow-50 border border-yellow-200 rounded-md px-3 py-2 text-sm text-yellow-800"
              data-testid="calendar-d3-alert"
            >
              ⚠️ {evt.stock_name || evt.title} 실적 발표 3일 전
            </div>
          ))}
        </div>
      )}

      {display.length === 0 ? (
        <p
          className="text-sm text-gray-400 text-center py-4"
          data-testid="calendar-widget-empty"
        >
          이번 주 예정된 이벤트가 없습니다
        </p>
      ) : (
        <div className="space-y-3" data-testid="calendar-widget-list">
          {display.map((evt) => (
            <div
              key={evt.id}
              className="flex items-start gap-2"
              data-testid="calendar-widget-item"
            >
              <span className="text-xs text-gray-500 shrink-0 mt-0.5 w-[72px]" data-testid="calendar-widget-date">
                {formatEventDate(evt.event_date)}
              </span>
              <span className="shrink-0">
                {EVENT_TYPE_ICONS[evt.event_type] || "📌"}
              </span>
              <p className="text-sm text-gray-800 flex-1 min-w-0 truncate">
                {evt.title}
              </p>
              {evt.is_tracked && (
                <span className="shrink-0" data-testid="calendar-widget-tracked">⭐</span>
              )}
            </div>
          ))}
        </div>
      )}

      {hasMore ? (
        <Link
          href="/calendar"
          className="block text-sm text-blue-600 hover:underline mt-4"
          data-testid="calendar-widget-more"
        >
          캘린더에서 더보기
        </Link>
      ) : (
        <Link
          href="/calendar"
          className="block text-sm text-blue-600 hover:underline mt-4"
          data-testid="calendar-widget-link"
        >
          마켓 캘린더 보기
        </Link>
      )}
    </div>
  );
}
