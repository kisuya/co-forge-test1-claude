"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { isLoggedIn } from "@/lib/auth";
import { stocksApi } from "@/lib/queries";
import type { StockDetail, StockHistoryResponse } from "@/types";
import EventTimeline from "@/components/EventTimeline";

const MARKET_BADGE: Record<string, string> = {
  KRX: "bg-blue-100 text-blue-700",
  NYSE: "bg-green-100 text-green-700",
  NASDAQ: "bg-purple-100 text-purple-700",
};

function formatPrice(price: number | null, currency: string | null): string {
  if (price === null) return "";
  if (currency === "KRW") {
    return `\u20A9${new Intl.NumberFormat("ko-KR").format(price)}`;
  }
  if (currency === "USD") {
    return `$${new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(price)}`;
  }
  return String(price);
}

function formatPriceChangePct(pct: number | null): string {
  if (pct === null) return "";
  const sign = pct > 0 ? "+" : "";
  const arrow = pct > 0 ? "\u25B2" : pct < 0 ? "\u25BC" : "";
  return `${arrow} ${sign}${pct.toFixed(1)}%`;
}

function getPriceChangeColor(pct: number | null): string {
  if (pct === null || pct === 0) return "text-gray-500";
  return pct > 0 ? "text-red-500" : "text-blue-500";
}

export default function StockDetailPage() {
  const router = useRouter();
  const params = useParams<{ stockId: string }>();
  const [stock, setStock] = useState<StockDetail | null>(null);
  const [history, setHistory] = useState<StockHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    if (!params.stockId) return;

    const fetchData = async () => {
      try {
        const [detailResp, historyResp] = await Promise.all([
          stocksApi.getDetail(params.stockId),
          stocksApi.getHistory(params.stockId),
        ]);
        setStock(detailResp.data);
        setHistory(historyResp.data);
      } catch (err: unknown) {
        const axiosErr = err as { response?: { status?: number } };
        if (axiosErr?.response?.status === 404) {
          setNotFound(true);
        } else {
          setError("종목 정보를 불러올 수 없습니다.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [router, params.stockId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center pt-24" data-testid="stock-detail-loading">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="min-h-screen bg-gray-50" data-testid="stock-not-found">
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 h-16 flex items-center gap-4">
            <button
              onClick={() => router.push("/dashboard")}
              className="text-sm text-gray-500 hover:text-gray-900"
              data-testid="back-button"
            >
              &larr; 대시보드
            </button>
          </div>
        </header>
        <main className="max-w-4xl mx-auto px-4 sm:px-6 py-16 text-center">
          <p className="text-6xl font-bold text-gray-300 mb-4">404</p>
          <p className="text-lg text-gray-700 mb-2">종목을 찾을 수 없습니다</p>
          <p className="text-sm text-gray-500 mb-6">요청하신 종목이 존재하지 않거나 삭제되었습니다.</p>
          <button
            onClick={() => router.push("/dashboard")}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            대시보드로 돌아가기
          </button>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50" data-testid="stock-detail-page">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-16 flex items-center gap-4">
          <button
            onClick={() => router.push("/dashboard")}
            className="text-sm text-gray-500 hover:text-gray-900"
            data-testid="back-button"
          >
            &larr; 대시보드
          </button>
          <h1 className="text-lg font-bold text-gray-900">종목 상세</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm" data-testid="error-message">
            {error}
          </div>
        )}

        {stock && (
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6" data-testid="stock-header">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900" data-testid="stock-name">
                  {stock.name}
                </h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-sm text-gray-500" data-testid="stock-code">
                    {stock.code}
                  </span>
                  <span
                    className={`px-2 py-0.5 text-xs rounded-full font-medium ${MARKET_BADGE[stock.market] || "bg-gray-100 text-gray-600"}`}
                    data-testid="market-badge"
                  >
                    {stock.market}
                  </span>
                </div>
              </div>
              <div className="text-right" data-testid="stock-price-section">
                {stock.latest_price !== null ? (
                  <>
                    <p className="text-xl font-bold text-gray-900" data-testid="stock-price">
                      {formatPrice(stock.latest_price, stock.price_currency)}
                    </p>
                    <p className={`text-sm ${getPriceChangeColor(stock.price_change_pct)}`} data-testid="stock-price-change">
                      {formatPriceChangePct(stock.price_change_pct)}
                    </p>
                  </>
                ) : (
                  <p className="text-sm text-gray-400 italic">시세 대기중</p>
                )}
              </div>
            </div>
            <div className="mt-3 flex items-center gap-3">
              {stock.tracking_count > 0 && (
                <span className="text-xs text-gray-400" data-testid="detail-tracking-count">
                  👥 {stock.tracking_count}명 추적 중
                </span>
              )}
            </div>
          </div>
        )}

        {/* Event timeline section - implemented in history-003 */}
        {history && (
          <EventTimeline history={history} stockId={params.stockId} />
        )}

        {/* Discussion section placeholder - implemented in community-004 */}
      </main>
    </div>
  );
}
