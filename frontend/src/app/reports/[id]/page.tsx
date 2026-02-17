"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { isLoggedIn } from "@/lib/auth";
import { reportsApi, shareApi } from "@/lib/queries";
import { addToast } from "@/lib/toast";
import type { Report } from "@/types";
import ReportView from "@/components/ReportView";

export default function ReportDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sharing, setSharing] = useState(false);
  const [fallbackUrl, setFallbackUrl] = useState("");
  const fallbackInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    if (!params.id) return;
    reportsApi
      .getById(params.id)
      .then((resp) => {
        setReport(resp.data);
        const name = resp.data.stock_name || "리포트";
        document.title = `${name} 변동 분석 | oh-my-stock`;
      })
      .catch(() => {
        setError("리포트를 불러오지 못했습니다.");
        document.title = "oh-my-stock";
      })
      .finally(() => setLoading(false));
  }, [router, params.id]);

  const handleShare = async () => {
    if (!params.id) return;
    setSharing(true);
    try {
      const resp = await shareApi.create(params.id);
      const url = resp.data.share_url;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(url);
        addToast("공유 링크가 복사되었습니다 (30일간 유효)", "success", 3000);
      } else {
        setFallbackUrl(url);
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number } };
      if (axiosErr?.response?.status === 403) {
        addToast("본인의 추적 종목 리포트만 공유할 수 있습니다", "error", 3000);
      } else {
        addToast("공유 링크 생성에 실패했습니다", "error", 3000);
      }
    } finally {
      setSharing(false);
    }
  };

  const handleFallbackCopy = () => {
    if (fallbackInputRef.current) {
      fallbackInputRef.current.select();
      document.execCommand("copy");
      addToast("공유 링크가 복사되었습니다 (30일간 유효)", "success", 3000);
      setFallbackUrl("");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center pt-24">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="text-sm text-gray-500 hover:text-gray-900"
            >
              &larr; 뒤로
            </button>
            <h1 className="text-lg font-bold text-gray-900">리포트 상세</h1>
          </div>
          {report && (
            <button
              onClick={handleShare}
              disabled={sharing}
              className="flex items-center gap-1.5 px-4 py-2 text-sm text-blue-600 hover:text-blue-700 border border-blue-200 rounded-lg hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="share-button"
            >
              {sharing ? (
                <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" data-testid="share-spinner" />
              ) : (
                <span>🔗</span>
              )}
              공유
            </button>
          )}
        </div>
      </header>
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}
        {report && <ReportView report={report} />}
      </main>

      {/* Clipboard fallback modal */}
      {fallbackUrl && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" data-testid="clipboard-fallback-modal">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">공유 링크</h3>
            <div className="flex gap-2">
              <input
                ref={fallbackInputRef}
                type="text"
                readOnly
                value={fallbackUrl}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm bg-gray-50"
                data-testid="fallback-url-input"
              />
              <button
                onClick={handleFallbackCopy}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
                data-testid="fallback-copy-button"
              >
                복사
              </button>
            </div>
            <button
              onClick={() => setFallbackUrl("")}
              className="mt-3 text-sm text-gray-500 hover:text-gray-700"
              data-testid="fallback-close-button"
            >
              닫기
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
