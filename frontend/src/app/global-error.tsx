"use client";

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ reset }: GlobalErrorProps) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center max-w-md" data-testid="global-error-boundary">
          <p className="text-5xl mb-4">&#x26A0;&#xFE0F;</p>
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            문제가 발생했습니다
          </h2>
          <p className="text-sm text-gray-500 mb-6">
            예상치 못한 오류가 발생했습니다. 다시 시도해주세요.
          </p>
          <button
            onClick={reset}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
            data-testid="global-error-reset-btn"
          >
            새로고침
          </button>
        </div>
      </body>
    </html>
  );
}
