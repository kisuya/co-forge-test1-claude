"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { isLoggedIn } from "@/lib/auth";
import { reportsApi } from "@/lib/queries";
import type { Report } from "@/types";
import AlertBadge from "@/components/AlertBadge";

export default function ReportsByStockPage() {
  const router = useRouter();
  const params = useParams<{ stockId: string }>();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    if (!params.stockId) return;
    reportsApi
      .getByStock(params.stockId)
      .then((resp) => setReports(resp.data))
      .catch(() => setError("리포트를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, [router, params.stockId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center pt-24">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  const stockName = reports.length > 0 ? reports[0].stock_name : "";

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
          <h1 className="text-lg font-bold text-gray-900">
            {stockName ? `${stockName} 리포트` : "종목 리포트"}
          </h1>
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
            <p className="text-lg">이 종목의 리포트가 없습니다</p>
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
                    {r.summary && (
                      <p className="text-sm text-gray-800 line-clamp-2">
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
