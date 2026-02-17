"use client";

import { useEffect, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { isLoggedIn, clearTokens } from "@/lib/auth";
import WatchlistManager from "@/components/WatchlistManager";
import NotificationPanel from "@/components/NotificationPanel";
import OnboardingOverlay from "@/components/OnboardingOverlay";

const BriefingCard = dynamic(() => import("@/components/BriefingCard"), { ssr: false });
const CalendarWidget = dynamic(() => import("@/components/CalendarWidget"), { ssr: false });
const NewsWidget = dynamic(() => import("@/components/NewsWidget"), { ssr: false });
const TrendingWidget = dynamic(() => import("@/components/TrendingWidget"), { ssr: false });

export default function DashboardPage() {
  const router = useRouter();
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
    }
    document.title = "내 관심 종목 | oh-my-stock";
  }, [router]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const pending = localStorage.getItem("onboarding_pending");
      if (pending === "true") {
        setShowOnboarding(true);
      }
    }
  }, []);

  const handleOnboardingComplete = useCallback(() => {
    setShowOnboarding(false);
  }, []);

  const handleStockClick = (stockId: string) => {
    router.push(`/reports/stock/${stockId}`);
  };

  const handleLogout = () => {
    clearTokens();
    router.replace("/login");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {showOnboarding && (
        <OnboardingOverlay onComplete={handleOnboardingComplete} />
      )}
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
        <BriefingCard />
        <CalendarWidget />
        <NewsWidget />
        {/* Mobile: trending widget above stockcards */}
        <div className="md:hidden">
          <TrendingWidget />
        </div>
        <div className="flex gap-6">
          <div className="flex-1 min-w-0">
            <WatchlistManager onStockClick={handleStockClick} />
          </div>
          {/* Desktop: trending widget as sidebar */}
          <div className="hidden md:block w-[280px] flex-shrink-0" data-testid="dashboard-sidebar">
            <TrendingWidget />
          </div>
        </div>
      </main>
    </div>
  );
}
