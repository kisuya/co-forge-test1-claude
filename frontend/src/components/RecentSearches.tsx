"use client";

import {
  getRecentSearches,
  removeRecentSearch,
  clearRecentSearches,
} from "@/lib/recentSearches";

interface RecentSearchesProps {
  onSelect: (query: string) => void;
  onUpdate: () => void;
}

export default function RecentSearches({
  onSelect,
  onUpdate,
}: RecentSearchesProps) {
  const searches = getRecentSearches();

  if (searches.length === 0) return null;

  const handleRemove = (q: string) => {
    removeRecentSearch(q);
    onUpdate();
  };

  const handleClearAll = () => {
    clearRecentSearches();
    onUpdate();
  };

  return (
    <div
      className="mt-2 border border-gray-200 rounded-lg"
      data-testid="recent-searches"
    >
      <ul className="divide-y divide-gray-100">
        {searches.map((q) => (
          <li
            key={q}
            className="flex items-center justify-between px-4 py-2 hover:bg-gray-50 cursor-pointer"
          >
            <button
              onClick={() => onSelect(q)}
              className="flex items-center gap-2 text-sm text-gray-700 flex-1 text-left"
              data-testid="recent-search-item"
            >
              <span className="text-gray-400">🕐</span>
              {q}
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleRemove(q);
              }}
              className="text-gray-400 hover:text-gray-600 text-sm ml-2"
              data-testid="remove-recent-btn"
              aria-label="최근 검색어 삭제"
            >
              ✕
            </button>
          </li>
        ))}
      </ul>
      <div className="px-4 py-2 border-t border-gray-100 text-right">
        <button
          onClick={handleClearAll}
          className="text-xs text-gray-400 hover:text-gray-600"
          data-testid="clear-all-recent"
        >
          최근 검색어 전체 삭제
        </button>
      </div>
    </div>
  );
}
