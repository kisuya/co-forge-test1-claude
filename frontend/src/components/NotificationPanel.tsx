"use client";

import { useState, useEffect, useCallback } from "react";
import { pushApi } from "@/lib/queries";
import { watchlistApi } from "@/lib/queries";
import type { WatchlistItem } from "@/types";
import { addToast } from "@/lib/toast";

const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || "";

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  const arr = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  return arr;
}

export default function NotificationPanel() {
  const [open, setOpen] = useState(false);
  const [online, setOnline] = useState(true);
  const [subscribed, setSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [permDenied, setPermDenied] = useState(false);

  useEffect(() => {
    setOnline(navigator.onLine);
    const goOnline = () => setOnline(true);
    const goOffline = () => setOnline(false);
    window.addEventListener("online", goOnline);
    window.addEventListener("offline", goOffline);
    return () => {
      window.removeEventListener("online", goOnline);
      window.removeEventListener("offline", goOffline);
    };
  }, []);

  const loadStatus = useCallback(async () => {
    try {
      const resp = await pushApi.status();
      setSubscribed(resp.data.subscribed);
    } catch {
      /* ignore */
    }
  }, []);

  const loadWatchlist = useCallback(async () => {
    try {
      const resp = await watchlistApi.getAll();
      setItems(resp.data);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    if (open) {
      loadStatus();
      loadWatchlist();
    }
  }, [open, loadStatus, loadWatchlist]);

  useEffect(() => {
    if (typeof Notification !== "undefined" && Notification.permission === "denied") {
      setPermDenied(true);
    }
  }, []);

  const handleSubscribe = async () => {
    setLoading(true);
    try {
      if (typeof Notification === "undefined" || !("serviceWorker" in navigator)) {
        addToast("이 브라우저는 알림을 지원하지 않습니다.", "error");
        return;
      }

      const perm = await Notification.requestPermission();
      if (perm !== "granted") {
        setPermDenied(true);
        addToast("브라우저 설정에서 알림을 허용해주세요.", "error");
        return;
      }
      setPermDenied(false);

      const reg = await navigator.serviceWorker.register("/sw.js");
      await navigator.serviceWorker.ready;

      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
      });

      const json = sub.toJSON();
      await pushApi.subscribe(
        json.endpoint!,
        json.keys!.p256dh!,
        json.keys!.auth!,
      );

      setSubscribed(true);
      addToast("알림이 활성화되었습니다.", "success");
    } catch {
      addToast("알림 설정에 실패했습니다.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleUnsubscribe = async () => {
    setLoading(true);
    try {
      const reg = await navigator.serviceWorker.getRegistration();
      const sub = reg ? await reg.pushManager.getSubscription() : null;
      if (sub) {
        await pushApi.unsubscribe(sub.endpoint);
        await sub.unsubscribe();
      }
      setSubscribed(false);
      addToast("알림이 비활성화되었습니다.", "info");
    } catch {
      addToast("알림 해제에 실패했습니다.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        data-testid="notification-bell"
        onClick={() => setOpen(!open)}
        className="relative text-gray-600 hover:text-gray-900 transition-colors"
        aria-label="알림 설정"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {subscribed && (
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-blue-500 rounded-full" />
        )}
      </button>

      {open && (
        <>
          <div
            data-testid="notification-overlay"
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
          />
          <div
            data-testid="notification-panel"
            className="fixed right-0 top-0 h-full w-80 bg-white shadow-xl z-50 overflow-y-auto animate-slide-left"
          >
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">알림 설정</h3>
                <button
                  data-testid="notification-close"
                  onClick={() => setOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  &#x2715;
                </button>
              </div>
            </div>

            {!online && (
              <div data-testid="offline-indicator" className="px-4 py-2 bg-yellow-50 text-yellow-700 text-sm">
                오프라인 상태입니다
              </div>
            )}

            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">전체 알림</p>
                  <p className="text-xs text-gray-500 mt-0.5">급변동 감지 시 푸시 알림</p>
                </div>
                <button
                  data-testid="global-toggle"
                  onClick={subscribed ? handleUnsubscribe : handleSubscribe}
                  disabled={loading}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    subscribed ? "bg-blue-600" : "bg-gray-300"
                  } ${loading ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      subscribed ? "translate-x-6" : "translate-x-1"
                    }`}
                  />
                </button>
              </div>
              {permDenied && (
                <p data-testid="perm-denied-msg" className="mt-2 text-xs text-red-600">
                  브라우저 설정에서 알림을 허용해주세요.{" "}
                  <a
                    href="https://support.google.com/chrome/answer/3220216"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline"
                  >
                    설정 가이드
                  </a>
                </p>
              )}
            </div>

            <div className="p-4">
              <p className="text-sm font-medium text-gray-700 mb-3">종목별 알림</p>
              {items.length === 0 ? (
                <p className="text-sm text-gray-400">관심 종목이 없습니다</p>
              ) : (
                <ul className="space-y-2" data-testid="stock-toggles">
                  {items.map((item) => (
                    <li key={item.id} className="flex items-center justify-between py-2">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{item.stock_name}</p>
                        <p className="text-xs text-gray-500">{item.stock_code}</p>
                      </div>
                      <div
                        className="relative inline-flex h-5 w-9 items-center rounded-full bg-blue-600"
                        data-testid={`stock-toggle-${item.stock_code}`}
                      >
                        <span className="inline-block h-3 w-3 transform rounded-full bg-white translate-x-5" />
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}
    </>
  );
}
