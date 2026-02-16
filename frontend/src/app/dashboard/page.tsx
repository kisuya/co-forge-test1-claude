"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isLoggedIn, clearTokens } from "@/lib/auth";
import WatchlistManager from "@/components/WatchlistManager";
import NotificationPanel from "@/components/NotificationPanel";

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
    }
  }, [router]);

  const handleStockClick = (stockId: string) => {
    router.push(`/reports/stock/${stockId}`);
  };

  const handleLogout = () => {
    clearTokens();
    router.replace("/login");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <h1 className="text-xl font-bold text-gray-900">oh-my-stock</h1>
            <nav className="flex items-center gap-4">
              <button
                onClick={() => router.push("/reports")}
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                리포트
              </button>
              <NotificationPanel />
              <button
                onClick={handleLogout}
                className="text-sm text-gray-500 hover:text-red-600 transition-colors"
              >
                로그아웃
              </button>
            </nav>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">대시보드</h2>
          <p className="text-sm text-gray-500 mt-1">
            관심 종목을 관리하고 급변동을 확인하세요
          </p>
        </div>
        <WatchlistManager onStockClick={handleStockClick} />
      </main>
    </div>
  );
}
