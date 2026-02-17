"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { stocksApi } from "@/lib/queries";
import { highlightMatch } from "@/lib/highlight";
import { addRecentSearch } from "@/lib/recentSearches";
import RecentSearches from "./RecentSearches";
import type { Stock } from "@/types";

interface StockSearchProps {
  onAdd: (stockId: string) => void;
  existingStockIds: Set<string>;
}

const DEBOUNCE_MS = 300;
const MIN_QUERY_LENGTH = 2;
const ADD_CLOSE_DELAY_MS = 500;

type MarketTab = "all" | "kr" | "us";

const MARKET_TABS: { key: MarketTab; label: string }[] = [
  { key: "all", label: "전체" },
  { key: "kr", label: "한국 🇰🇷" },
  { key: "us", label: "미국 🇺🇸" },
];

const MARKET_BADGE: Record<string, string> = {
  KRX: "bg-blue-100 text-blue-700",
  NYSE: "bg-green-100 text-green-700",
  NASDAQ: "bg-purple-100 text-purple-700",
};

export default function StockSearch({ onAdd, existingStockIds }: StockSearchProps) {
  const [query, setQuery] = useState("");
  const [market, setMarket] = useState<MarketTab>("all");
  const [results, setResults] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [searched, setSearched] = useState(false);
  const [addedId, setAddedId] = useState<string | null>(null);
  const [focused, setFocused] = useState(false);
  const [recentKey, setRecentKey] = useState(0);
  const abortRef = useRef<AbortController | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const marketRef = useRef<MarketTab>(market);
  marketRef.current = market;

  const executeSearch = useCallback(async (q: string) => {
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError("");
    setSearched(false);
    try {
      const resp = await stocksApi.search(q, marketRef.current, controller.signal);
      if (!controller.signal.aborted) {
        setResults(resp.data);
        setShowResults(true);
        setSearched(true);
        setLoading(false);
        if (resp.data.length > 0) addRecentSearch(q);
      }
    } catch (err: unknown) {
      if (!controller.signal.aborted) {
        const isAbort = err instanceof Error && err.name === "CanceledError";
        if (!isAbort) setError("검색에 실패했습니다.");
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < MIN_QUERY_LENGTH) {
      setResults([]);
      setShowResults(false);
      setSearched(false);
      setLoading(false);
      if (abortRef.current) { abortRef.current.abort(); abortRef.current = null; }
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => executeSearch(trimmed), DEBOUNCE_MS);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, market, executeSearch]);

  useEffect(() => { return () => { if (abortRef.current) abortRef.current.abort(); }; }, []);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowResults(false);
        setFocused(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") { setShowResults(false); setFocused(false); }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  const handleAdd = (stockId: string) => {
    onAdd(stockId);
    setAddedId(stockId);
    setTimeout(() => { setShowResults(false); setAddedId(null); }, ADD_CLOSE_DELAY_MS);
  };

  const handleRecentSelect = (q: string) => {
    setQuery(q);
    setFocused(false);
  };

  const showHint = query.trim().length > 0 && query.trim().length < MIN_QUERY_LENGTH;
  const trimmedQuery = query.trim();
  const noResults = searched && results.length === 0 && !loading;
  const showRecent = focused && query.trim().length === 0 && !showResults;

  return (
    <div className="mb-6" data-testid="stock-search" ref={containerRef}>
      <div className="flex gap-2 mb-3" data-testid="market-tabs">
        {MARKET_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setMarket(tab.key)}
            className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
              market === tab.key
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
            data-testid={`market-tab-${tab.key}`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setFocused(true)}
          placeholder="종목명 또는 코드 검색"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none pr-10"
          data-testid="search-input"
          aria-label="종목 검색"
        />
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2" data-testid="search-spinner">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />
          </div>
        )}
      </div>
      {showHint && (
        <p className="mt-2 text-sm text-gray-400" data-testid="min-length-hint">2글자 이상 입력하세요</p>
      )}
      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
      {showRecent && (
        <RecentSearches key={recentKey} onSelect={handleRecentSelect} onUpdate={() => setRecentKey((k) => k + 1)} />
      )}
      {showResults && noResults && (
        <div className="mt-3 p-4 border border-gray-200 rounded-lg text-center" data-testid="no-results">
          <p className="text-gray-500">검색 결과가 없습니다</p>
          <p className="text-sm text-gray-400 mt-1">종목코드를 직접 입력해보세요 (예: 005930)</p>
        </div>
      )}
      {showResults && results.length > 0 && (
        <ul className="mt-3 border border-gray-200 rounded-lg divide-y divide-gray-100" data-testid="search-results">
          {results.map((stock) => {
            const alreadyAdded = existingStockIds.has(stock.id);
            const justAdded = addedId === stock.id;
            const nameParts = highlightMatch(stock.name, trimmedQuery);
            const codeParts = highlightMatch(stock.code, trimmedQuery);
            const nameKrParts = stock.name_kr ? highlightMatch(stock.name_kr, trimmedQuery) : null;
            const badgeClass = MARKET_BADGE[stock.market] || "bg-gray-100 text-gray-600";
            return (
              <li key={stock.id} className="flex items-center justify-between px-4 py-3 hover:bg-gray-50">
                <div>
                  <span className="font-medium text-gray-900">
                    {nameParts.map((p, i) => p.bold ? <strong key={i} className="text-blue-600">{p.text}</strong> : <span key={i}>{p.text}</span>)}
                  </span>
                  {nameKrParts && (
                    <span className="ml-1 text-sm text-gray-600" data-testid="name-kr">
                      ({nameKrParts.map((p, i) => p.bold ? <strong key={i} className="text-blue-600">{p.text}</strong> : <span key={i}>{p.text}</span>)})
                    </span>
                  )}
                  <span className="ml-2 text-sm text-gray-500">
                    {codeParts.map((p, i) => p.bold ? <strong key={i} className="text-blue-600">{p.text}</strong> : <span key={i}>{p.text}</span>)}
                  </span>
                  <span className={`ml-2 px-1.5 py-0.5 text-xs rounded font-medium ${badgeClass}`} data-testid="market-badge">
                    {stock.market}
                  </span>
                </div>
                {justAdded ? (
                  <span className="text-green-500 text-lg" data-testid="check-animation">✓</span>
                ) : alreadyAdded ? (
                  <span className="px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded" data-testid="already-added-badge">추가됨</span>
                ) : (
                  <button onClick={() => handleAdd(stock.id)} className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors" data-testid="add-stock-btn">+ 추가</button>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
