"use client";

import type { WatchlistItem } from "@/types";

interface StockCardProps {
  item: WatchlistItem;
  changePct?: number;
  onRemove: (itemId: string) => void;
  onClick?: () => void;
}

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
  onClick,
}: StockCardProps) {
  const isSpike =
    changePct !== undefined && (changePct >= 3 || changePct <= -3);
  const colorClass = getChangeColor(changePct);
  const baseClass = isSpike
    ? `border-2 ${colorClass}`
    : "border border-gray-200";

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
            {item.stock_name}
          </h3>
          <p className="text-sm text-gray-500">{item.stock_code}</p>
        </div>
        <div className="text-right ml-4">
          <p className={`text-lg font-bold ${colorClass}`}>
            {formatChange(changePct)}
          </p>
          {isSpike && (
            <span className="inline-block px-2 py-0.5 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
              급변동
            </span>
          )}
        </div>
      </div>
      <div className="mt-2 flex items-center justify-between">
        <span className="text-xs text-gray-400">
          임계값: ±{item.threshold}%
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRemove(item.id);
          }}
          className="text-xs text-gray-400 hover:text-red-500 transition-colors"
          aria-label={`${item.stock_name} 제거`}
        >
          제거
        </button>
      </div>
    </div>
  );
}
