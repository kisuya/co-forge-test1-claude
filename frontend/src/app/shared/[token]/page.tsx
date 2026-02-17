"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { shareApi } from "@/lib/queries";
import type { SharedReportResponse, Report } from "@/types";
import ReportView from "@/components/ReportView";

function toReport(data: SharedReportResponse): Report {
  return {
    id: "",
    stock_id: "",
    stock_code: data.stock_code,
    stock_name: data.stock_name,
    trigger_change_pct: 0,
    summary: data.report.summary,
    analysis: {
      summary: data.report.summary || "",
      causes: data.report.causes.map((c) => ({
        reason: c.reason || c.description || "",
        confidence: (c.confidence as "high" | "medium" | "low") || "low",
        impact: c.impact || "",
      })),
    },
    status: "completed",
    sources: data.report.sources.map((s, i) => ({
      id: String(i),
      source_type: s.source_type,
      title: s.title,
      url: s.url,
    })),
    created_at: data.report.created_at,
    completed_at: null,
  };
}

export default function SharedReportPage() {
  const params = useParams<{ token: string }>();
  const [data, setData] = useState<SharedReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [expired, setExpired] = useState(false);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!params.token) return;
    shareApi
      .getShared(params.token)
      .then((resp) => setData(resp.data))
      .catch((err: unknown) => {
        const axiosErr = err as { response?: { status?: number } };
        if (axiosErr?.response?.status === 410) {
          setExpired(true);
        } else {
          setNotFound(true);
        }
      })
      .finally(() => setLoading(false));
  }, [params.token]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50" data-testid="shared-page-loading">
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 h-14 flex items-center">
            <a href="/" className="text-lg font-bold text-blue-600" data-testid="shared-logo">
              oh-my-stock
            </a>
            <span className="ml-2 text-sm text-gray-400">공유 리포트</span>
          </div>
        </header>
        <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
          <div className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse" data-testid="shared-skeleton">
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-4" />
            <div className="h-4 bg-gray-200 rounded w-2/3 mb-2" />
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
            <div className="h-4 bg-gray-200 rounded w-3/4" />
          </div>
        </main>
      </div>
    );
  }

  if (expired) {
    return (
      <div className="min-h-screen bg-gray-50" data-testid="shared-expired">
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 h-14 flex items-center">
            <a href="/" className="text-lg font-bold text-blue-600" data-testid="shared-logo">
              oh-my-stock
            </a>
            <span className="ml-2 text-sm text-gray-400">공유 리포트</span>
          </div>
        </header>
        <main className="max-w-4xl mx-auto px-4 sm:px-6 py-16 text-center">
          <p className="text-5xl mb-4">🕐</p>
          <p className="text-xl font-semibold text-gray-800 mb-2" data-testid="expired-title">
            이 공유 링크는 만료되었습니다
          </p>
          <p className="text-sm text-gray-500 mb-6">공유 링크의 유효 기간이 지났습니다.</p>
          <a
            href="/"
            className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            data-testid="expired-home-link"
          >
            oh-my-stock 방문하기
          </a>
        </main>
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="min-h-screen bg-gray-50" data-testid="shared-not-found">
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 h-14 flex items-center">
            <a href="/" className="text-lg font-bold text-blue-600" data-testid="shared-logo">
              oh-my-stock
            </a>
            <span className="ml-2 text-sm text-gray-400">공유 리포트</span>
          </div>
        </header>
        <main className="max-w-4xl mx-auto px-4 sm:px-6 py-16 text-center">
          <p className="text-6xl font-bold text-gray-300 mb-4">404</p>
          <p className="text-lg text-gray-700 mb-2">공유 리포트를 찾을 수 없습니다</p>
          <p className="text-sm text-gray-500 mb-6">잘못된 링크이거나 삭제된 리포트입니다.</p>
          <a
            href="/"
            className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            oh-my-stock 방문하기
          </a>
        </main>
      </div>
    );
  }

  if (!data) return null;

  const report = toReport(data);

  return (
    <div className="min-h-screen bg-gray-50" data-testid="shared-report-page">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-14 flex items-center">
          <a href="/" className="text-lg font-bold text-blue-600" data-testid="shared-logo">
            oh-my-stock
          </a>
          <span className="ml-2 text-sm text-gray-400">공유 리포트</span>
        </div>
      </header>

      {/* OG meta info */}
      <title>{`${data.stock_name} 변동 분석 | oh-my-stock`}</title>
      <meta name="description" content={data.report.summary || ""} />
      <meta property="og:title" content={`${data.stock_name} 변동 분석 | oh-my-stock`} data-testid="og-title" />
      <meta property="og:description" content={data.report.summary || ""} data-testid="og-description" />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div className="mb-3">
          <span className="text-xs text-gray-400" data-testid="shared-market-badge">
            {data.market}
          </span>
        </div>

        <ReportView report={report} shareMode />

        {/* CTA banner */}
        <div
          className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6 text-center"
          data-testid="cta-banner"
        >
          <p className="text-lg font-semibold text-gray-800 mb-2">
            더 많은 분석을 보려면 가입하세요
          </p>
          <p className="text-sm text-gray-500 mb-4">
            실시간 변동 감지, 맞춤 알림, 히스토리 분석을 무료로 이용하세요.
          </p>
          <a
            href="/signup"
            className="inline-block px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            data-testid="cta-signup-link"
          >
            무료 회원가입
          </a>
        </div>
      </main>
    </div>
  );
}
