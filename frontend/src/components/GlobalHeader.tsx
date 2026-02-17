"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { isLoggedIn } from "@/lib/auth";
import { profileApi } from "@/lib/queries";
import NotificationBell from "@/components/NotificationBell";

export default function GlobalHeader() {
  const router = useRouter();
  const pathname = usePathname();
  const [authChecked, setAuthChecked] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [displayName, setDisplayName] = useState("");

  // Shared pages show mini header
  const isSharedPage = pathname?.startsWith("/shared");

  useEffect(() => {
    const checkAuth = async () => {
      const authenticated = isLoggedIn();
      setLoggedIn(authenticated);
      if (authenticated) {
        try {
          const res = await profileApi.get();
          setDisplayName(res.data.display_name || res.data.email.split("@")[0]);
        } catch {
          setDisplayName("");
        }
      }
      setAuthChecked(true);
    };
    checkAuth();
  }, [pathname]);

  if (isSharedPage) {
    return null; // Shared pages have their own mini header
  }

  const navLinks = [
    { href: "/dashboard", label: "대시보드" },
    { href: "/mypage", label: "마이페이지" },
  ];

  const avatarLetter = displayName ? displayName[0].toUpperCase() : "U";

  return (
    <header
      data-testid="global-header"
      className="sticky top-0 z-50 bg-white border-b border-gray-200"
      style={{ height: "64px" }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full">
        <div className="flex items-center justify-between h-full">
          {/* Left: Logo */}
          <Link
            href={loggedIn ? "/dashboard" : "/"}
            data-testid="header-logo"
            className="text-xl font-bold text-gray-900 hover:text-gray-700"
          >
            oh-my-stock
          </Link>

          {/* Center: Nav links (desktop only) */}
          <nav
            data-testid="desktop-nav"
            className="hidden md:flex items-center gap-6"
            aria-label="메인 내비게이션"
          >
            {navLinks.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  data-testid={`nav-${link.href.replace("/", "")}`}
                  className={`text-sm transition-colors ${
                    isActive
                      ? "font-bold text-gray-900 border-b-2 border-gray-900 pb-1"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Right: Auth-dependent */}
          <div className="flex items-center gap-3">
            {!authChecked ? (
              <div data-testid="auth-skeleton" className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse" />
              </div>
            ) : loggedIn ? (
              <div data-testid="header-auth-logged-in" className="flex items-center gap-3">
                {/* Notification bell */}
                <div data-testid="notification-bell-placeholder">
                  <NotificationBell />
                </div>
                {/* Profile icon */}
                <button
                  data-testid="header-profile-icon"
                  onClick={() => router.push("/mypage")}
                  className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-bold hover:bg-blue-700"
                  aria-label="마이페이지"
                >
                  {avatarLetter}
                </button>
              </div>
            ) : (
              <div data-testid="header-auth-guest" className="flex items-center gap-3">
                <Link
                  href="/login"
                  data-testid="header-login-link"
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  로그인
                </Link>
                <Link
                  href="/signup"
                  data-testid="header-signup-btn"
                  className="text-sm px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  시작하기
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
