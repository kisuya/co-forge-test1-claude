const STORAGE_KEY = "recent_searches";
const MAX_ITEMS = 10;

export function getRecentSearches(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function addRecentSearch(query: string): void {
  if (typeof window === "undefined") return;
  const searches = getRecentSearches().filter((s) => s !== query);
  searches.unshift(query);
  if (searches.length > MAX_ITEMS) searches.pop();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(searches));
}

export function removeRecentSearch(query: string): void {
  if (typeof window === "undefined") return;
  const searches = getRecentSearches().filter((s) => s !== query);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(searches));
}

export function clearRecentSearches(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}
