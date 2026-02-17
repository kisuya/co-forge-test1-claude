"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/dashboard", icon: "🏠", label: "대시보드" },
  { href: "/news", icon: "📰", label: "뉴스" },
  { href: "/mypage", icon: "👤", label: "마이페이지" },
];

export default function MobileNav() {
  const pathname = usePathname();

  // Hide on shared pages
  const isSharedPage = pathname?.startsWith("/shared");
  if (isSharedPage) return null;

  return (
    <nav
      data-testid="mobile-nav"
      className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 md:hidden"
      style={{ height: "56px", paddingBottom: "env(safe-area-inset-bottom)" }}
      aria-label="모바일 내비게이션"
    >
      <div className="flex items-center justify-around h-full">
        {tabs.map((tab) => {
          const isActive = pathname === tab.href || pathname?.startsWith(tab.href + "/");
          return (
            <Link
              key={tab.href}
              href={tab.href}
              data-testid={`mobile-tab-${tab.href.replace("/", "")}`}
              className={`flex flex-col items-center justify-center gap-0.5 ${
                isActive ? "text-blue-600" : "text-gray-500"
              }`}
              aria-label={tab.label}
              aria-current={isActive ? "page" : undefined}
            >
              <span className="text-xl" data-testid={`tab-icon-${tab.href.replace("/", "")}`}>
                {tab.icon}
              </span>
              <span
                className="text-[10px]"
                data-testid={`tab-label-${tab.href.replace("/", "")}`}
              >
                {tab.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
