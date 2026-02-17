"use client";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorBoundary({ error, reset }: ErrorProps) {
  return (
    <div
      className="min-h-screen bg-gray-50 flex items-center justify-center px-4"
      data-testid="error-boundary"
    >
      <div className="text-center max-w-md">
        <p className="text-5xl mb-4">&#x26A0;&#xFE0F;</p>
        <h2
          className="font-bold text-gray-900 mb-2"
          data-testid="error-title"
          style={{ fontSize: "24px" }}
        >
          문제가 발생했습니다
        </h2>
        <p
          className="text-gray-500 mb-6"
          data-testid="error-description"
          style={{ fontSize: "14px" }}
        >
          잠시 후 다시 시도해주세요
        </p>
        {process.env.NODE_ENV === "development" && error.message && (
          <pre
            className="text-xs text-left bg-gray-100 p-3 rounded mb-4 overflow-auto max-h-32 text-red-600"
            data-testid="error-stack"
          >
            {error.message}
          </pre>
        )}
        <div className="flex flex-col items-center gap-3">
          <button
            onClick={reset}
            className="px-6 py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            data-testid="error-reset-btn"
            style={{ borderRadius: "var(--radius-md, 8px)" }}
          >
            새로고침
          </button>
          <a
            href="/dashboard"
            className="text-sm text-gray-500 hover:text-gray-700"
            data-testid="error-dashboard-link"
          >
            대시보드로 돌아가기
          </a>
        </div>
      </div>
    </div>
  );
}
