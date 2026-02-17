"use client";

import { useState, useEffect, useCallback } from "react";

interface OnboardingOverlayProps {
  onComplete: () => void;
}

export default function OnboardingOverlay({ onComplete }: OnboardingOverlayProps) {
  const [step, setStep] = useState(1);
  const [visible, setVisible] = useState(true);

  const handleSkip = useCallback(() => {
    localStorage.removeItem("onboarding_pending");
    setVisible(false);
    onComplete();
  }, [onComplete]);

  const handleNext = useCallback(() => {
    if (step >= 3) {
      handleSkip();
    } else {
      setStep((s) => s + 1);
    }
  }, [step, handleSkip]);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        handleSkip();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleSkip]);

  if (!visible) return null;

  return (
    <div
      data-testid="onboarding-overlay"
      className="fixed inset-0 z-50"
      style={{ backgroundColor: "rgba(0,0,0,0.5)" }}
    >
      {/* Step 1: Welcome modal */}
      {step === 1 && (
        <div
          data-testid="onboarding-step-1"
          className="fixed inset-0 flex items-center justify-center z-50"
        >
          <div
            data-testid="onboarding-welcome-modal"
            className="bg-white rounded-lg shadow-xl p-8 max-w-md mx-4 text-center"
            style={{ borderRadius: "var(--radius-lg, 12px)" }}
            role="dialog"
            aria-label="온보딩 환영"
          >
            <div className="text-5xl mb-4">🎉</div>
            <h2
              data-testid="onboarding-welcome-title"
              className="text-2xl font-bold text-gray-900 mb-2"
            >
              환영합니다!
            </h2>
            <p
              data-testid="onboarding-welcome-desc"
              className="text-gray-600 mb-6"
            >
              관심 종목의 급변동을 AI가 분석해드립니다
            </p>
            <button
              data-testid="onboarding-start-btn"
              onClick={handleNext}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              style={{ borderRadius: "var(--radius-md, 8px)" }}
            >
              시작하기
            </button>
            <div className="mt-4">
              <button
                data-testid="onboarding-skip"
                onClick={handleSkip}
                className="text-sm text-gray-400 hover:text-gray-600"
              >
                건너뛰기
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Highlight search area */}
      {step === 2 && (
        <div
          data-testid="onboarding-step-2"
          className="fixed inset-0 flex items-start justify-center z-50"
          style={{ paddingTop: "120px" }}
        >
          <div
            data-testid="onboarding-search-tooltip"
            className="bg-white rounded-lg shadow-xl p-6 max-w-sm mx-4 text-center"
            style={{ borderRadius: "var(--radius-lg, 12px)" }}
            role="dialog"
            aria-label="온보딩 검색 안내"
          >
            <div className="text-3xl mb-3">🔍</div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">
              관심 종목을 추가해보세요
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              검색창에서 종목을 찾아 관심목록에 추가할 수 있습니다
            </p>
            <div className="flex items-center justify-between">
              <button
                data-testid="onboarding-skip"
                onClick={handleSkip}
                className="text-sm text-gray-400 hover:text-gray-600"
              >
                건너뛰기
              </button>
              <button
                data-testid="onboarding-next-btn"
                onClick={handleNext}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors"
                style={{ borderRadius: "var(--radius-md, 8px)" }}
              >
                다음
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 3: StockCard highlight */}
      {step === 3 && (
        <div
          data-testid="onboarding-step-3"
          className="fixed inset-0 flex items-center justify-center z-50"
        >
          <div
            data-testid="onboarding-stockcard-tooltip"
            className="bg-white rounded-lg shadow-xl p-6 max-w-sm mx-4 text-center"
            style={{ borderRadius: "var(--radius-lg, 12px)" }}
            role="dialog"
            aria-label="온보딩 종목카드 안내"
          >
            <div className="text-3xl mb-3">📊</div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">
              급변동이 감지되면 AI가 분석합니다
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              종목의 주가가 급변동하면 자동으로 원인을 분석한 리포트를 제공합니다
            </p>
            <button
              data-testid="onboarding-complete-btn"
              onClick={handleSkip}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors w-full"
              style={{ borderRadius: "var(--radius-md, 8px)" }}
            >
              시작하기
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
