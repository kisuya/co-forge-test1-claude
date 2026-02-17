"use client";

import { useEffect, useState } from "react";
import { calendarApi } from "@/lib/queries";
import { isLoggedIn } from "@/lib/auth";
import type { CalendarEvent } from "@/types";
import Skeleton from "@/components/Skeleton";

const DAY_NAMES = ["월", "화", "수", "목", "금", "토", "일"];

const EVENT_DOT_COLORS: Record<string, string> = {
  earnings: "bg-green-500",
  economic: "bg-blue-500",
  central_bank: "bg-red-500",
  dividend: "bg-purple-500",
};

const EVENT_TYPE_LABELS: Record<string, string> = {
  earnings: "실적",
  economic: "경제",
  central_bank: "금리",
  dividend: "배당",
};

const EVENT_BADGE_COLORS: Record<string, string> = {
  earnings: "bg-green-100 text-green-700",
  economic: "bg-blue-100 text-blue-700",
  central_bank: "bg-red-100 text-red-700",
  dividend: "bg-purple-100 text-purple-700",
};

function getMonthDays(year: number, month: number): (number | null)[][] {
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  // Convert Sunday=0 to Monday-based (Mon=0)
  const startOffset = firstDay === 0 ? 6 : firstDay - 1;

  const weeks: (number | null)[][] = [];
  let currentWeek: (number | null)[] = [];

  for (let i = 0; i < startOffset; i++) {
    currentWeek.push(null);
  }

  for (let day = 1; day <= daysInMonth; day++) {
    currentWeek.push(day);
    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  }

  if (currentWeek.length > 0) {
    while (currentWeek.length < 7) {
      currentWeek.push(null);
    }
    weeks.push(currentWeek);
  }

  return weeks;
}

function formatDate(year: number, month: number, day: number): string {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

export default function CalendarPage() {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth());
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [marketFilter, setMarketFilter] = useState<"ALL" | "KR" | "US">("ALL");
  const [trackedOnly, setTrackedOnly] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    document.title = "마켓 캘린더 | oh-my-stock";
    setLoggedIn(isLoggedIn());
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);

    const startDate = formatDate(year, month, 1);
    const lastDay = new Date(year, month + 1, 0).getDate();
    const endDate = formatDate(year, month, lastDay);

    calendarApi
      .list(startDate, endDate, marketFilter)
      .then((res) => {
        if (!cancelled) setEvents(res.data);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [year, month, marketFilter]);

  const weeks = getMonthDays(year, month);
  const todayStr = formatDate(
    today.getFullYear(),
    today.getMonth(),
    today.getDate()
  );

  // Filter and group events by date
  const filteredEvents = trackedOnly ? events.filter((e) => e.is_tracked) : events;
  const eventsByDate: Record<string, CalendarEvent[]> = {};
  for (const evt of filteredEvents) {
    if (!eventsByDate[evt.event_date]) {
      eventsByDate[evt.event_date] = [];
    }
    eventsByDate[evt.event_date].push(evt);
  }

  const selectedEvents = selectedDate ? eventsByDate[selectedDate] || [] : [];

  const goPrev = () => {
    if (month === 0) {
      setYear(year - 1);
      setMonth(11);
    } else {
      setMonth(month - 1);
    }
    setSelectedDate(null);
  };

  const goNext = () => {
    if (month === 11) {
      setYear(year + 1);
      setMonth(0);
    } else {
      setMonth(month + 1);
    }
    setSelectedDate(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1
            className="text-2xl font-bold text-gray-900"
            data-testid="calendar-page-title"
          >
            📅 마켓 캘린더
          </h1>
        </div>

        {/* Market tabs */}
        <div className="flex items-center gap-3 mb-6" data-testid="calendar-market-tabs">
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
                data-testid={`calendar-market-${m.toLowerCase()}`}
              >
                {m === "ALL" ? "전체" : m === "KR" ? "한국" : "미국"}
              </button>
            ))}
          </div>
        </div>

        {/* Tracked only toggle */}
        <div className="flex items-center gap-3 mb-6" data-testid="calendar-tracked-filter">
          {loggedIn ? (
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={trackedOnly}
                onChange={(e) => setTrackedOnly(e.target.checked)}
                className="rounded border-gray-300 text-blue-600"
                data-testid="calendar-tracked-toggle"
              />
              <span className="text-sm text-gray-700">내 종목만</span>
            </label>
          ) : (
            <p className="text-sm text-gray-400" data-testid="calendar-login-prompt">
              로그인하면 관심 종목 일정을 확인할 수 있습니다
            </p>
          )}
        </div>

        {/* Tracked filter empty state */}
        {!loading && !error && trackedOnly && filteredEvents.length === 0 && (
          <div className="text-center py-8" data-testid="calendar-tracked-empty">
            <p className="text-sm text-gray-400">관심 종목 관련 이벤트가 없습니다</p>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="text-center py-16" data-testid="calendar-error">
            <p className="text-lg text-gray-600">캘린더를 불러올 수 없습니다</p>
            <button
              onClick={() => {
                setError(false);
                setLoading(true);
                const startDate = formatDate(year, month, 1);
                const lastDay = new Date(year, month + 1, 0).getDate();
                const endDate = formatDate(year, month, lastDay);
                calendarApi
                  .list(startDate, endDate, marketFilter)
                  .then((res) => setEvents(res.data))
                  .catch(() => setError(true))
                  .finally(() => setLoading(false));
              }}
              className="mt-3 px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
              data-testid="calendar-retry"
            >
              다시 시도
            </button>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div data-testid="calendar-skeleton">
            <Skeleton width="100%" height={400} />
          </div>
        )}

        {/* Calendar */}
        {!loading && !error && (
          <div className="flex flex-col md:flex-row gap-6">
            {/* Calendar grid */}
            <div className="flex-1">
              {/* Month navigation */}
              <div
                className="flex items-center justify-between mb-4"
                data-testid="calendar-nav"
              >
                <button
                  onClick={goPrev}
                  className="p-2 hover:bg-gray-100 rounded-md"
                  aria-label="이전 달"
                  data-testid="calendar-prev"
                >
                  &lt;
                </button>
                <h2
                  className="text-lg font-bold text-gray-900"
                  data-testid="calendar-month-label"
                >
                  {year}년 {month + 1}월
                </h2>
                <button
                  onClick={goNext}
                  className="p-2 hover:bg-gray-100 rounded-md"
                  aria-label="다음 달"
                  data-testid="calendar-next"
                >
                  &gt;
                </button>
              </div>

              {/* Day headers */}
              <div
                className="grid grid-cols-7 gap-0 mb-1"
                data-testid="calendar-grid"
              >
                {DAY_NAMES.map((d) => (
                  <div
                    key={d}
                    className="text-center text-xs font-medium text-gray-500 py-2"
                  >
                    {d}
                  </div>
                ))}

                {/* Date cells */}
                {weeks.flat().map((day, idx) => {
                  if (day === null) {
                    return <div key={`empty-${idx}`} className="p-1 min-h-[48px]" />;
                  }
                  const dateStr = formatDate(year, month, day);
                  const dayEvents = eventsByDate[dateStr] || [];
                  const isToday = dateStr === todayStr;
                  const isSelected = dateStr === selectedDate;
                  const hasTracked = dayEvents.some((e) => e.is_tracked);

                  return (
                    <button
                      key={dateStr}
                      className={`p-1 min-h-[48px] text-center relative hover:bg-gray-100 rounded-md transition-colors ${
                        isSelected ? "bg-blue-50 ring-1 ring-blue-300" : ""
                      }`}
                      onClick={() => setSelectedDate(dateStr)}
                      data-testid="calendar-date-cell"
                    >
                      <span
                        className={`text-sm inline-flex items-center justify-center w-7 h-7 rounded-full ${
                          isToday
                            ? "bg-blue-600 text-white"
                            : "text-gray-700"
                        }`}
                        data-testid={isToday ? "calendar-today" : undefined}
                      >
                        {day}
                      </span>
                      {dayEvents.length > 0 && (
                        <div className="flex gap-0.5 justify-center mt-0.5" data-testid="calendar-event-dots">
                          {Array.from(new Set(dayEvents.map((e) => e.event_type))).map(
                            (type) => (
                              <span
                                key={type}
                                className={`w-1.5 h-1.5 rounded-full ${
                                  hasTracked && dayEvents.some((e) => e.event_type === type && e.is_tracked)
                                    ? "bg-yellow-400"
                                    : EVENT_DOT_COLORS[type] || "bg-gray-400"
                                }`}
                                data-testid="calendar-dot"
                              />
                            )
                          )}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Event detail panel (desktop sidebar / mobile bottom) */}
            <div
              className="md:w-[280px] md:flex-shrink-0"
              data-testid="calendar-detail-panel"
            >
              {selectedDate ? (
                <div className="bg-white rounded-lg border border-gray-200 p-4">
                  <h3 className="text-sm font-bold text-gray-900 mb-3" data-testid="calendar-detail-date">
                    {selectedDate}
                  </h3>
                  {selectedEvents.length === 0 ? (
                    <p
                      className="text-sm text-gray-400 text-center py-4"
                      data-testid="calendar-no-events"
                    >
                      예정된 이벤트가 없습니다
                    </p>
                  ) : (
                    <div className="space-y-3" data-testid="calendar-event-list">
                      {selectedEvents.map((evt) => (
                        <div
                          key={evt.id}
                          className={`p-3 rounded-md border ${
                            evt.is_tracked
                              ? "bg-yellow-50 border-yellow-200"
                              : "bg-gray-50 border-gray-100"
                          }`}
                          data-testid="calendar-event-item"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span
                              className={`text-xs px-2 py-0.5 rounded-full ${
                                EVENT_BADGE_COLORS[evt.event_type] || "bg-gray-100 text-gray-700"
                              }`}
                              data-testid="calendar-event-type-badge"
                            >
                              {EVENT_TYPE_LABELS[evt.event_type] || evt.event_type}
                            </span>
                            {evt.is_tracked && (
                              <span
                                className="text-xs text-yellow-600"
                                data-testid="calendar-tracked-badge"
                              >
                                내 관심 종목
                              </span>
                            )}
                          </div>
                          <p className="text-sm font-medium text-gray-900" data-testid="calendar-event-title">
                            {evt.title}
                          </p>
                          {evt.description && (
                            <p className="text-xs text-gray-500 mt-1">
                              {evt.description}
                            </p>
                          )}
                          {evt.stock_name && (
                            <p className="text-xs text-gray-400 mt-1">
                              {evt.stock_name}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
                  <p className="text-sm text-gray-400 py-4">
                    날짜를 선택하면 이벤트를 확인할 수 있습니다
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
