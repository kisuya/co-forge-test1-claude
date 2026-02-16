"use client";

import { useState } from "react";
import { watchlistApi } from "@/lib/queries";
import type { WatchlistItem } from "@/types";

interface StockCardProps {
  item: WatchlistItem;
  changePct?: number;
  onRemove: (itemId: string) => void;
  onThresholdChange?: (itemId: string, threshold: number) => void;
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

export default function StockCard({
  item,
  changePct,
  onRemove,
  onThresholdChange,
  onClick,
}: StockCardProps) {
  const [showSettings, setShowSettings] = useState(false);
  const [threshold, setThreshold] = useState(item.threshold);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<"success" | "error" | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  const isSpike = changePct !== undefined && (changePct >= 3 || changePct <= -3);
  const colorClass = getChangeColor(changePct);
  const baseClass = isSpike ? `border-2 ${colorClass}` : "border border-gray-200";
  const isDefault = threshold === DEFAULT_THRESHOLD;

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

  return (
    <div
      className={`rounded-lg p-4 ${baseClass} cursor-pointer hover:shadow-md transition-shadow`}
      onClick={onClick}
      role="article"
      data-testid="stock-card"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">{item.stock_name}</h3>
          <div className="flex items-center gap-1.5">
            <span className="text-sm text-gray-500">{item.stock_code}</span>
            <span className={`px-1.5 py-0.5 text-xs rounded font-medium ${MARKET_BADGE[item.stock_market] || "bg-gray-100 text-gray-600"}`} data-testid="card-market-badge">
              {item.stock_market}
            </span>
          </div>
        </div>
        <div className="text-right ml-4">
          <p className={`text-lg font-bold ${colorClass}`}>{formatChange(changePct)}</p>
          {isSpike && (
            <span className="inline-block px-2 py-0.5 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">급변동</span>
          )}
        </div>
      </div>
      <div className="mt-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`text-xs ${isDefault ? "text-gray-400" : "text-gray-600"}`}>
            임계값: ±{threshold}%
          </span>
          <button
            onClick={(e) => { e.stopPropagation(); setShowSettings(!showSettings); }}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            data-testid="settings-icon"
            aria-label="임계값 설정"
          >
            ⚙️
          </button>
          {feedback === "success" && (
            <span className="text-green-500 text-sm" data-testid="threshold-success">✓</span>
          )}
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onRemove(item.id); }}
          className="text-xs text-gray-400 hover:text-red-500 transition-colors"
          aria-label={`${item.stock_name} 제거`}
        >
          제거
        </button>
      </div>
      {showSettings && (
        <div
          className="mt-3 p-3 bg-gray-50 rounded-lg"
          onClick={(e) => e.stopPropagation()}
          data-testid="threshold-panel"
        >
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() => handleThresholdChange(threshold - STEP)}
              disabled={saving || threshold <= MIN_THRESHOLD}
              className="w-8 h-8 flex items-center justify-center rounded-full bg-white border border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="threshold-decrease"
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
            >
              +
            </button>
          </div>
          <p className="text-xs text-gray-400 text-center mt-1">0.5% 단위 (1%~10%)</p>
          {errorMsg && <p className="text-xs text-red-500 text-center mt-1" data-testid="threshold-error">{errorMsg}</p>}
        </div>
      )}
    </div>
  );
}
