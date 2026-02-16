"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { isLoggedIn } from "@/lib/auth";
import { reportsApi } from "@/lib/queries";
import type { Report } from "@/types";
import AlertBadge from "@/components/AlertBadge";

export default function ReportsListPage() {
  const router = useRouter();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    reportsApi
      .getAll()
      .then((resp) => setReports(resp.data))
      .catch(() => setError("리포트를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, [router]);

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
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-16 flex items-center gap-4">
          <button
            onClick={() => router.push("/dashboard")}
            className="text-sm text-gray-500 hover:text-gray-900"
          >
            &larr; 대시보드
          </button>
          <h1 className="text-lg font-bold text-gray-900">분석 리포트</h1>
        </div>
      </header>
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}
        {reports.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">아직 리포트가 없습니다</p>
            <p className="text-sm mt-1">
              관심 종목에 급변동이 발생하면 자동으로 생성됩니다
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((r) => (
              <button
                key={r.id}
                onClick={() => router.push(`/reports/${r.id}`)}
                className="w-full text-left bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div className="min-w-0">
                    <p className="font-semibold text-gray-900 truncate">
                      {r.stock_name}
                      <span className="ml-2 text-sm font-normal text-gray-500">
                        {r.stock_code}
                      </span>
                    </p>
                    {r.summary && (
                      <p className="text-sm text-gray-600 mt-1 line-clamp-1">
                        {r.summary}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <AlertBadge changePct={r.trigger_change_pct} />
                    {r.created_at && (
                      <span className="text-xs text-gray-400">
                        {new Date(r.created_at).toLocaleDateString("ko-KR")}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
