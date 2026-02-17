"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { getAccessToken } from "@/lib/auth";

interface Notification {
  id: number;
  report_id: number;
  stock_name: string;
  change_pct: number;
  created_at: string;
  is_read: boolean;
}

export default function NotificationBell() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [hasUnread, setHasUnread] = useState(false);
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const token = getAccessToken();
        const res = await fetch("/api/notifications?limit=5", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          const items = data.data || data || [];
          setNotifications(items);
          setHasUnread(items.some((n: Notification) => !n.is_read));
        }
      } catch {
        // Silently fail
      }
    };
    fetchNotifications();
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={dropdownRef} className="relative" data-testid="notification-bell-container">
      <button
        data-testid="notification-bell"
        onClick={() => setOpen(!open)}
        className="relative w-8 h-8 flex items-center justify-center text-gray-600 hover:text-gray-900"
        aria-label="알림"
      >
        <span className="text-xl">🔔</span>
        {hasUnread && (
          <span
            data-testid="notification-unread-dot"
            className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"
          />
        )}
      </button>

      {open && (
        <div
          data-testid="notification-dropdown"
          className="absolute right-0 top-10 bg-white border border-gray-200 rounded-lg shadow-lg z-50"
          style={{ width: "300px" }}
        >
          {notifications.length === 0 ? (
            <div
              data-testid="notification-empty"
              className="p-4 text-center text-sm text-gray-500"
            >
              새로운 알림이 없습니다
            </div>
          ) : (
            <div data-testid="notification-list">
              {notifications.map((n) => (
                <Link
                  key={n.id}
                  href={`/reports/${n.report_id}`}
                  data-testid="notification-item"
                  className="block px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                  onClick={() => setOpen(false)}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900">
                      {n.stock_name}
                    </span>
                    <span
                      className={`text-sm font-semibold ${
                        n.change_pct > 0 ? "text-red-500" : "text-blue-500"
                      }`}
                    >
                      {n.change_pct > 0 ? "+" : ""}
                      {n.change_pct.toFixed(2)}%
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {new Date(n.created_at).toLocaleDateString("ko-KR")}
                  </div>
                </Link>
              ))}
            </div>
          )}
          <div className="border-t border-gray-100 p-2 text-center">
            <Link
              href="/notifications"
              data-testid="notification-view-all"
              className="text-sm text-blue-600 hover:underline"
              onClick={() => setOpen(false)}
            >
              모든 알림 보기
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
