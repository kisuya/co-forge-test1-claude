"use client";

import { useEffect, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { isLoggedIn } from "@/lib/auth";
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

  return (
    <div className="min-h-screen bg-gray-50">
      {showOnboarding && (
        <OnboardingOverlay onComplete={handleOnboardingComplete} />
      )}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">대시보드</h2>
            <p className="text-sm text-gray-500 mt-1">
              관심 종목을 관리하고 급변동을 확인하세요
            </p>
          </div>
          <nav className="flex items-center gap-3" aria-label="대시보드 알림 설정">
            <NotificationPanel />
          </nav>
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
