"use client";

import { useState, useEffect, useCallback } from "react";
import { watchlistApi } from "@/lib/queries";
import type { WatchlistItem } from "@/types";
import StockCard from "./StockCard";
import StockSearch from "./StockSearch";

interface WatchlistManagerProps {
  onStockClick?: (stockId: string) => void;
}

export default function WatchlistManager({
  onStockClick,
}: WatchlistManagerProps) {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchWatchlist = useCallback(async () => {
    try {
      const resp = await watchlistApi.getAll();
      setItems(resp.data);
    } catch {
      setError("관심목록을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWatchlist();
  }, [fetchWatchlist]);

  const handleAdd = async (stockId: string) => {
    try {
      const resp = await watchlistApi.add(stockId);
      setItems((prev) => [...prev, resp.data]);
    } catch {
      setError("종목 추가에 실패했습니다.");
    }
  };

  const handleRemove = async (itemId: string) => {
    try {
      await watchlistApi.remove(itemId);
      setItems((prev) => prev.filter((i) => i.id !== itemId));
    } catch {
      setError("종목 제거에 실패했습니다.");
    }
  };

  const existingStockIds = new Set(items.map((i) => i.stock_id));

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div data-testid="watchlist-manager">
      <StockSearch onAdd={handleAdd} existingStockIds={existingStockIds} />
      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}
      {items.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg">관심 종목이 없습니다</p>
          <p className="text-sm mt-1">위에서 종목을 검색하여 추가해보세요</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((item) => (
            <StockCard
              key={item.id}
              item={item}
              onRemove={handleRemove}
              onClick={() => onStockClick?.(item.stock_id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
