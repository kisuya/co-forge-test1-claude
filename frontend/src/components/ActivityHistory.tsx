"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { profileApi } from "@/lib/queries";
import type { ProfileReportItem, ProfileDiscussionItem } from "@/types";

type TabType = "reports" | "discussions";

export default function ActivityHistory() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>("reports");
  const [reports, setReports] = useState<ProfileReportItem[]>([]);
  const [discussions, setDiscussions] = useState<ProfileDiscussionItem[]>([]);
  const [reportsPage, setReportsPage] = useState(1);
  const [discussionsPage, setDiscussionsPage] = useState(1);
  const [hasMoreReports, setHasMoreReports] = useState(false);
  const [hasMoreDiscussions, setHasMoreDiscussions] = useState(false);
  const [loadingReports, setLoadingReports] = useState(false);
  const [loadingDiscussions, setLoadingDiscussions] = useState(false);

  useEffect(() => {
    fetchReports(1);
    fetchDiscussions(1);
  }, []);

  const fetchReports = async (page: number) => {
    setLoadingReports(true);
    try {
      const res = await profileApi.getReports(page);
      if (page === 1) {
        setReports(res.data.items);
      } else {
        setReports((prev) => [...prev, ...res.data.items]);
      }
      setHasMoreReports(res.data.has_more);
      setReportsPage(page);
    } catch {
      // silently fail
    } finally {
      setLoadingReports(false);
    }
  };

  const fetchDiscussions = async (page: number) => {
    setLoadingDiscussions(true);
    try {
      const res = await profileApi.getDiscussions(page);
      if (page === 1) {
        setDiscussions(res.data.items);
      } else {
        setDiscussions((prev) => [...prev, ...res.data.items]);
      }
      setHasMoreDiscussions(res.data.has_more);
      setDiscussionsPage(page);
    } catch {
      // silently fail
    } finally {
      setLoadingDiscussions(false);
    }
  };

  const formatRelativeTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    if (days > 0) return `${days}일 전`;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours > 0) return `${hours}시간 전`;
    const mins = Math.floor(diff / (1000 * 60));
    if (mins > 0) return `${mins}분 전`;
    return "방금 전";
  };

  return (
    <div data-testid="activity-history" className="bg-white rounded-lg shadow-sm mb-6">
      <div className="px-6 pt-4">
        <h2 className="text-lg font-bold text-gray-900 mb-3">최근 활동</h2>
        <div data-testid="activity-tabs" className="flex border-b border-gray-200" role="tablist" aria-label="활동 내역 탭">
          <button
            data-testid="tab-reports"
            onClick={() => setActiveTab("reports")}
            className={`px-4 py-2 text-sm font-medium border-b-2 ${
              activeTab === "reports"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
            role="tab"
            aria-selected={activeTab === "reports"}
            aria-label="리포트 탭"
          >
            리포트
          </button>
          <button
            data-testid="tab-discussions"
            onClick={() => setActiveTab("discussions")}
            className={`px-4 py-2 text-sm font-medium border-b-2 ${
              activeTab === "discussions"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
            role="tab"
            aria-selected={activeTab === "discussions"}
            aria-label="토론 탭"
          >
            토론
          </button>
        </div>
      </div>

      <div className="p-6">
        {activeTab === "reports" && (
          <div data-testid="reports-list">
            {reports.length === 0 && !loadingReports ? (
              <p data-testid="empty-reports" className="text-gray-400 text-sm text-center py-6">
                아직 활동 이력이 없습니다
              </p>
            ) : (
              <ul className="space-y-3">
                {reports.map((report) => (
                  <li
                    key={report.id}
                    data-testid="report-item"
                    onClick={() => router.push(`/reports/${report.id}`)}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 cursor-pointer"
                  >
                    <div>
                      <span className="text-sm font-medium text-gray-900">
                        {report.stock_name}
                      </span>
                      <span
                        className={`ml-2 text-sm font-bold ${
                          report.change_pct >= 0 ? "text-red-500" : "text-blue-500"
                        }`}
                      >
                        {report.change_pct >= 0 ? "▲" : "▼"}
                        {Math.abs(report.change_pct).toFixed(1)}%
                      </span>
                    </div>
                    <span className="text-xs text-gray-400">
                      {formatRelativeTime(report.created_at)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            {hasMoreReports && (
              <button
                data-testid="load-more-reports"
                onClick={() => fetchReports(reportsPage + 1)}
                disabled={loadingReports}
                className="w-full mt-4 py-2 text-sm text-blue-600 hover:text-blue-700 disabled:opacity-50"
              >
                {loadingReports ? "로딩 중..." : "더 보기"}
              </button>
            )}
          </div>
        )}

        {activeTab === "discussions" && (
          <div data-testid="discussions-list">
            {discussions.length === 0 && !loadingDiscussions ? (
              <p data-testid="empty-discussions" className="text-gray-400 text-sm text-center py-6">
                아직 활동 이력이 없습니다
              </p>
            ) : (
              <ul className="space-y-3">
                {discussions.map((discussion) => (
                  <li
                    key={discussion.id}
                    data-testid="discussion-item"
                    onClick={() => router.push(`/stocks/${discussion.stock_id}`)}
                    className="p-3 rounded-lg hover:bg-gray-50 cursor-pointer"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900">
                        {discussion.stock_name}
                      </span>
                      <span className="text-xs text-gray-400">
                        {formatRelativeTime(discussion.created_at)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 truncate">
                      {discussion.content}
                    </p>
                  </li>
                ))}
              </ul>
            )}
            {hasMoreDiscussions && (
              <button
                data-testid="load-more-discussions"
                onClick={() => fetchDiscussions(discussionsPage + 1)}
                disabled={loadingDiscussions}
                className="w-full mt-4 py-2 text-sm text-blue-600 hover:text-blue-700 disabled:opacity-50"
              >
                {loadingDiscussions ? "로딩 중..." : "더 보기"}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
