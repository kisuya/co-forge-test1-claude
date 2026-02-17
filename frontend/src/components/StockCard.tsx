"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { watchlistApi } from "@/lib/queries";
import { addToast } from "@/lib/toast";
import type { WatchlistItem } from "@/types";

interface StockCardProps {
  item: WatchlistItem;
  changePct?: number;
  onRemove: (itemId: string) => void;
  onThresholdChange?: (itemId: string, threshold: number) => void;
  onAlertChange?: (itemId: string, enabled: boolean) => void;
  onClick?: () => void;
}

const STEP = 0.5;
const MIN_THRESHOLD = 1;
const MAX_THRESHOLD = 10;
const DEFAULT_THRESHOLD = 3;

const MARKET_BADGE: Record<string, string> = {
  KRX: "bg-blue-100 text-blue-700",
  NYSE: "bg-green-100 text-green-700",
  NASDAQ: "bg-purple-100 text-purple-700",
};

function getChangeColor(pct: number | undefined): string {
  if (pct === undefined) return "text-gray-500";
  if (pct >= 3) return "text-red-600 bg-red-50 border-red-200";
  if (pct <= -3) return "text-blue-600 bg-blue-50 border-blue-200";
  if (pct > 0) return "text-red-500";
  if (pct < 0) return "text-blue-500";
  return "text-gray-500";
}

function formatChange(pct: number | undefined): string {
  if (pct === undefined) return "-";
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(2)}%`;
}

function formatPrice(price: number | null, currency: string | null): string {
  if (price === null) return "";
  if (currency === "KRW") {
    return `₩${new Intl.NumberFormat("ko-KR").format(price)}`;
  }
  if (currency === "USD") {
    return `$${new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(price)}`;
  }
  return String(price);
}

function formatPriceChange(change: number | null, pct: number | null): string {
  if (change === null || pct === null) return "";
  const sign = change > 0 ? "+" : "";
  const arrow = change > 0 ? "▲" : change < 0 ? "▼" : "";
  return `${arrow}${sign}${new Intl.NumberFormat("ko-KR").format(Math.abs(change))} (${sign}${pct.toFixed(1)}%)`;
}

function getPriceChangeColor(change: number | null): string {
  if (change === null || change === 0) return "text-gray-500";
  return change > 0 ? "text-red-500" : "text-blue-500";
}

function formatRelativeTime(isoString: string | null): string {
  if (!isoString) return "";
  const now = new Date();
  const updated = new Date(isoString);
  const diffMs = now.getTime() - updated.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "방금 전";
  if (diffMin < 60) return `${diffMin}분 전`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour}시간 전`;
  const diffDay = Math.floor(diffHour / 24);
  return `${diffDay}일 전`;
}

export default function StockCard({
  item,
  changePct,
  onRemove,
  onThresholdChange,
  onAlertChange,
  onClick,
}: StockCardProps) {
  const router = useRouter();
  const [showSettings, setShowSettings] = useState(false);
  const [threshold, setThreshold] = useState(item.threshold);
  const [alertEnabled, setAlertEnabled] = useState(item.alert_enabled);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<"success" | "error" | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [showConfirmDelete, setShowConfirmDelete] = useState(false);
  const [menuFocusIndex, setMenuFocusIndex] = useState(-1);
  const [isMobile, setIsMobile] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  // Detect mobile viewport (max-width: 768px)
  useEffect(() => {
    const mql = window.matchMedia("(max-width: 768px)");
    setIsMobile(mql.matches);
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  // Lock body scroll when bottom sheet is open on mobile
  useEffect(() => {
    if (showSettings && isMobile) {
      document.body.style.overflow = "hidden";
      return () => { document.body.style.overflow = ""; };
    }
  }, [showSettings, isMobile]);

  const isSpike = changePct !== undefined && (changePct >= 3 || changePct <= -3);
  const colorClass = getChangeColor(changePct);
  const baseClass = isSpike ? `border-2 ${colorClass}` : "border border-gray-200";

  const closeMenu = useCallback(() => {
    setShowSettings(false);
    setShowConfirmDelete(false);
    setMenuFocusIndex(-1);
  }, []);

  // Close menu on outside click
  useEffect(() => {
    if (!showSettings) return;
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        closeMenu();
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [showSettings, closeMenu]);

  // Close menu on Escape + arrow key navigation
  useEffect(() => {
    if (!showSettings) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        closeMenu();
        menuButtonRef.current?.focus();
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setMenuFocusIndex((prev) => Math.min(prev + 1, 3));
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setMenuFocusIndex((prev) => Math.max(prev - 1, 0));
      }
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [showSettings, closeMenu]);

  const handleThresholdChange = async (newVal: number) => {
    const clamped = Math.round(Math.max(MIN_THRESHOLD, Math.min(MAX_THRESHOLD, newVal)) * 10) / 10;
    const prevVal = threshold;
    setThreshold(clamped);
    setSaving(true);
    setFeedback(null);
    setErrorMsg("");
    try {
      await watchlistApi.updateThreshold(item.id, clamped);
      setFeedback("success");
      onThresholdChange?.(item.id, clamped);
      setTimeout(() => setFeedback(null), 1000);
    } catch {
      setThreshold(prevVal);
      setFeedback("error");
      setErrorMsg("연결 실패, 다시 시도해주세요");
      setTimeout(() => { setFeedback(null); setErrorMsg(""); }, 3000);
    } finally {
      setSaving(false);
    }
  };

  const handleAlertToggle = async () => {
    const newVal = !alertEnabled;
    try {
      await watchlistApi.updateAlert(item.id, newVal);
      setAlertEnabled(newVal);
      onAlertChange?.(item.id, newVal);
      addToast(newVal ? "알림이 켜졌습니다" : "알림이 꺼졌습니다", "success");
    } catch {
      addToast("알림 설정에 실패했습니다", "error");
    }
  };

  const handleRemoveConfirm = () => {
    onRemove(item.id);
    closeMenu();
  };

  return (
    <div
      className={`rounded-lg p-4 ${baseClass} cursor-pointer hover:shadow-md transition-shadow`}
      onClick={onClick}
      role="article"
      data-testid="stock-card"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">
            <span
              onClick={(e) => { e.stopPropagation(); router.push(`/stocks/${item.stock_id}`); }}
              className="cursor-pointer hover:underline"
              data-testid="stock-name-link"
            >
              {item.stock_name}
            </span>
          </h3>
          <div className="flex items-center gap-1.5">
            <span className="text-sm text-gray-500">{item.stock_code}</span>
            <span className={`px-1.5 py-0.5 text-xs rounded font-medium ${MARKET_BADGE[item.stock_market] || "bg-gray-100 text-gray-600"}`} data-testid="card-market-badge">
              {item.stock_market}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-right" data-testid="price-section">
            {item.is_price_available ? (
              <>
                <p className="text-lg font-bold text-gray-900" data-testid="current-price">
                  {formatPrice(item.latest_price, item.price_currency)}
                </p>
                <p className={`text-sm ${getPriceChangeColor(item.price_change)}`} data-testid="price-change">
                  {formatPriceChange(item.price_change, item.price_change_pct)}
                </p>
              </>
            ) : (
              <p className="text-sm text-gray-400 italic" data-testid="price-unavailable">시세 대기중</p>
            )}
            {item.is_price_available && item.price_freshness === "stale" && (
              <span className="text-yellow-500 text-xs" data-testid="stale-warning" title="업데이트 지연">⚠</span>
            )}
          </div>
          {/* Kebab menu */}
          <div className="relative" ref={menuRef}>
            <button
              ref={menuButtonRef}
              onClick={(e) => { e.stopPropagation(); setShowSettings(!showSettings); }}
              className="text-gray-400 hover:text-gray-600 transition-colors text-xl px-1 leading-none"
              data-testid="kebab-menu-button"
              data-settings-icon="settings-icon"
              aria-label="종목 관리 메뉴"
              aria-haspopup="menu"
              aria-expanded={showSettings}
            >
              ⋮
            </button>

            {/* Desktop dropdown menu (hidden on mobile via CSS) */}
            {showSettings && !isMobile && (
              <div
                className="absolute right-0 top-full mt-1 w-60 bg-white border border-gray-200 rounded-lg shadow-lg z-50 hidden md:block"
                role="menu"
                data-testid="kebab-dropdown"
              >
                <button
                  onClick={(e) => { e.stopPropagation(); closeMenu(); router.push(`/stocks/${item.stock_id}`); }}
                  className={`w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 rounded-t-lg ${menuFocusIndex === 0 ? "bg-gray-50" : ""}`}
                  role="menuitem"
                  data-testid="menu-history"
                >
                  📊 이벤트 히스토리
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); handleAlertToggle(); }}
                  className={`w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 ${menuFocusIndex === 1 ? "bg-gray-50" : ""}`}
                  role="menuitem"
                  data-testid="menu-alert-toggle"
                >
                  🔔 알림 {alertEnabled ? "OFF" : "ON"}
                </button>
                <div className="px-4 py-1 text-xs text-gray-400" data-testid="alert-status">
                  알림: {alertEnabled ? "켜짐" : "꺼짐"}
                </div>
                <div
                  className="px-4 py-3 border-t border-gray-100"
                  onClick={(e) => e.stopPropagation()}
                  data-testid="threshold-panel"
                >
                  <p className="text-sm text-gray-700 mb-2">⚙️ 변동 감지 임계값</p>
                  <div className="flex items-center justify-center gap-3">
                    <button
                      onClick={() => handleThresholdChange(threshold - STEP)}
                      disabled={saving || threshold <= MIN_THRESHOLD}
                      className="w-8 h-8 flex items-center justify-center rounded-full bg-white border border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                      data-testid="threshold-decrease"
                      aria-label="임계값 감소"
                    >
                      −
                    </button>
                    <span className="text-lg font-semibold min-w-[3rem] text-center" data-testid="threshold-value">
                      {threshold}%
                    </span>
                    <button
                      onClick={() => handleThresholdChange(threshold + STEP)}
                      disabled={saving || threshold >= MAX_THRESHOLD}
                      className="w-8 h-8 flex items-center justify-center rounded-full bg-white border border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                      data-testid="threshold-increase"
                      aria-label="임계값 증가"
                    >
                      +
                    </button>
                  </div>
                  <p className="text-xs text-gray-400 text-center mt-1">0.5% 단위 (1%~10%)</p>
                  {feedback === "success" && (
                    <p className="text-xs text-green-500 text-center mt-1" data-testid="threshold-success">✓ 저장됨</p>
                  )}
                  {errorMsg && <p className="text-xs text-red-500 text-center mt-1" data-testid="threshold-error">{errorMsg}</p>}
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); setShowConfirmDelete(true); }}
                  className={`w-full text-left px-4 py-3 text-sm text-red-500 hover:bg-gray-50 rounded-b-lg border-t border-gray-100 ${menuFocusIndex === 3 ? "bg-gray-50" : ""}`}
                  role="menuitem"
                  data-testid="menu-remove"
                >
                  🗑️ 관심목록에서 제거
                </button>
              </div>
            )}
          </div>

          {/* Mobile bottom sheet (shown on mobile only) */}
          {showSettings && isMobile && (
            <div
              className="fixed inset-0 z-50 md:hidden"
              data-testid="bottomsheet-overlay"
              onClick={(e) => { e.stopPropagation(); closeMenu(); }}
            >
              <div className="absolute inset-0 bg-black/50" />
              <div
                className="absolute bottom-0 left-0 right-0 bg-white rounded-t-2xl pb-[env(safe-area-inset-bottom)] animate-slide-up"
                onClick={(e) => e.stopPropagation()}
                data-testid="bottomsheet-content"
                role="menu"
              >
                <div className="w-10 h-1 bg-gray-300 rounded-full mx-auto mt-3 mb-2" data-testid="bottomsheet-handle" />
                <div className="px-4 py-2 border-b border-gray-100">
                  <h3 className="text-base font-semibold text-gray-900">{item.stock_name}</h3>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); closeMenu(); router.push(`/stocks/${item.stock_id}`); }}
                  className="w-full text-left px-4 py-4 text-sm text-gray-700 hover:bg-gray-50 min-h-[48px]"
                  role="menuitem"
                  data-testid="bs-menu-history"
                >
                  📊 이벤트 히스토리
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); handleAlertToggle(); }}
                  className="w-full text-left px-4 py-4 text-sm text-gray-700 hover:bg-gray-50 min-h-[48px]"
                  role="menuitem"
                  data-testid="bs-menu-alert-toggle"
                >
                  🔔 알림 {alertEnabled ? "OFF" : "ON"} ({alertEnabled ? "켜짐" : "꺼짐"})
                </button>
                <div
                  className="px-4 py-4 border-t border-gray-100"
                  onClick={(e) => e.stopPropagation()}
                  data-testid="bs-threshold-panel"
                >
                  <p className="text-sm text-gray-700 mb-2">⚙️ 변동 감지 임계값</p>
                  <div className="flex items-center justify-center gap-3">
                    <button
                      onClick={() => handleThresholdChange(threshold - STEP)}
                      disabled={saving || threshold <= MIN_THRESHOLD}
                      className="w-10 h-10 flex items-center justify-center rounded-full bg-white border border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-50 min-h-[48px]"
                      aria-label="임계값 감소"
                    >
                      −
                    </button>
                    <span className="text-lg font-semibold min-w-[3rem] text-center">
                      {threshold}%
                    </span>
                    <button
                      onClick={() => handleThresholdChange(threshold + STEP)}
                      disabled={saving || threshold >= MAX_THRESHOLD}
                      className="w-10 h-10 flex items-center justify-center rounded-full bg-white border border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-50 min-h-[48px]"
                      aria-label="임계값 증가"
                    >
                      +
                    </button>
                  </div>
                  <p className="text-xs text-gray-400 text-center mt-1">0.5% 단위 (1%~10%)</p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); setShowConfirmDelete(true); }}
                  className="w-full text-left px-4 py-4 text-sm text-red-500 hover:bg-gray-50 border-t border-gray-100 min-h-[48px]"
                  role="menuitem"
                  data-testid="bs-menu-remove"
                >
                  🗑️ 관심목록에서 제거
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mt-1 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {item.tracking_count > 0 && (
            <span className="text-xs text-gray-400" data-testid="tracking-count">
              👥 {item.tracking_count >= 100 ? "100명+ 추적 중" : `${item.tracking_count}명 추적 중`}
            </span>
          )}
          {item.is_price_available && item.price_updated_at && (
            <span className="text-[10px] text-gray-400" data-testid="price-updated-at">
              {formatRelativeTime(item.price_updated_at)}
            </span>
          )}
        </div>
        {changePct !== undefined && (
          <div>
            <span className={`text-lg font-bold ${colorClass}`}>{formatChange(changePct)}</span>
            {isSpike && (
              <span className="inline-block ml-1 px-2 py-0.5 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">급변동</span>
            )}
          </div>
        )}
      </div>

      {/* Delete confirmation dialog */}
      {showConfirmDelete && (
        <div
          className="fixed inset-0 flex items-center justify-center z-[60] bg-black/30"
          onClick={(e) => { e.stopPropagation(); setShowConfirmDelete(false); }}
          data-testid="confirm-delete-overlay"
        >
          <div
            className="bg-white rounded-lg p-6 shadow-xl max-w-sm mx-4"
            onClick={(e) => e.stopPropagation()}
            data-testid="confirm-delete-dialog"
            role="dialog"
            aria-label="종목 제거 확인"
          >
            <h4 className="text-lg font-semibold text-gray-900 mb-2">종목 제거</h4>
            <p className="text-sm text-gray-600 mb-4">
              {item.stock_name}을(를) 관심목록에서 제거하시겠습니까?
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowConfirmDelete(false)}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
                data-testid="confirm-cancel"
              >
                취소
              </button>
              <button
                onClick={handleRemoveConfirm}
                className="px-4 py-2 text-sm text-white bg-red-500 hover:bg-red-600 rounded-lg"
                data-testid="confirm-delete"
              >
                제거
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
