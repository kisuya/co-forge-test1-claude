"use client";

import { useState, useCallback } from "react";
import { stocksApi } from "@/lib/queries";
import type { Stock } from "@/types";

interface StockSearchProps {
  onAdd: (stockId: string) => void;
  existingStockIds: Set<string>;
}

export default function StockSearch({
  onAdd,
  existingStockIds,
}: StockSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = useCallback(async () => {
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    setError("");
    try {
      const resp = await stocksApi.search(q);
      setResults(resp.data);
    } catch {
      setError("검색에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }, [query]);

  return (
    <div className="mb-6" data-testid="stock-search">
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="종목명 또는 종목코드 검색..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
        />
        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "검색중..." : "검색"}
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
      {results.length > 0 && (
        <ul className="mt-3 border border-gray-200 rounded-lg divide-y divide-gray-100">
          {results.map((stock) => {
            const alreadyAdded = existingStockIds.has(stock.id);
            return (
              <li
                key={stock.id}
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-50"
              >
                <div>
                  <span className="font-medium text-gray-900">
                    {stock.name}
                  </span>
                  <span className="ml-2 text-sm text-gray-500">
                    {stock.code}
                  </span>
                  <span className="ml-2 text-xs text-gray-400">
                    {stock.market}
                  </span>
                </div>
                <button
                  onClick={() => onAdd(stock.id)}
                  disabled={alreadyAdded}
                  className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  {alreadyAdded ? "추가됨" : "추가"}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
