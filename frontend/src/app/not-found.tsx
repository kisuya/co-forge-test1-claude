"use client";

import { isLoggedIn } from "@/lib/auth";

export default function NotFoundPage() {
  const loggedIn = typeof window !== "undefined" && isLoggedIn();

  return (
    <div
      className="min-h-screen bg-gray-50 flex items-center justify-center px-4"
      data-testid="not-found-page"
    >
      <div className="text-center max-w-md">
        <p
          className="font-bold text-gray-300 mb-4"
          data-testid="not-found-code"
          style={{ fontSize: "72px" }}
        >
          404
        </p>
        <h2
          className="font-bold text-gray-900 mb-2"
          data-testid="not-found-title"
          style={{ fontSize: "24px" }}
        >
          페이지를 찾을 수 없습니다
        </h2>
        <p
          className="text-gray-500 mb-6"
          data-testid="not-found-description"
          style={{ fontSize: "14px" }}
        >
          요청하신 페이지가 존재하지 않거나 이동되었습니다
        </p>
        {loggedIn ? (
          <a
            href="/dashboard"
            className="inline-block px-6 py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            data-testid="not-found-dashboard-link"
            style={{ borderRadius: "var(--radius-md, 8px)" }}
          >
            대시보드로 돌아가기
          </a>
        ) : (
          <a
            href="/"
            className="inline-block px-6 py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            data-testid="not-found-home-link"
            style={{ borderRadius: "var(--radius-md, 8px)" }}
          >
            홈으로 돌아가기
          </a>
        )}
      </div>
    </div>
  );
}
