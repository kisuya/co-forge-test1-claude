"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { isLoggedIn } from "@/lib/auth";
import { reportsApi } from "@/lib/queries";
import type { Report } from "@/types";
import ReportView from "@/components/ReportView";

export default function ReportDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    if (!params.id) return;
    reportsApi
      .getById(params.id)
      .then((resp) => setReport(resp.data))
      .catch(() => setError("리포트를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, [router, params.id]);

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
            onClick={() => router.back()}
            className="text-sm text-gray-500 hover:text-gray-900"
          >
            &larr; 뒤로
          </button>
          <h1 className="text-lg font-bold text-gray-900">리포트 상세</h1>
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
    </div>
  );
}
