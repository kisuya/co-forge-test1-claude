"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isLoggedIn } from "@/lib/auth";
import { profileApi } from "@/lib/queries";
import type { ProfileResponse } from "@/types";
import { addToast } from "@/lib/toast";
import NicknameEditor from "@/components/NicknameEditor";
import PasswordChangeForm from "@/components/PasswordChangeForm";
import ActivityHistory from "@/components/ActivityHistory";

export default function MyPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    fetchProfile();
  }, [router]);

  const fetchProfile = async () => {
    setLoading(true);
    setError(false);
    try {
      const res = await profileApi.get();
      setProfile(res.data);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const handleNicknameUpdate = (updated: ProfileResponse) => {
    setProfile(updated);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-3xl mx-auto px-4 py-8">
          <div data-testid="mypage-skeleton" className="animate-pulse">
            <div className="bg-white rounded-lg p-6 mb-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-gray-200 rounded-full" />
                <div className="flex-1">
                  <div className="h-5 bg-gray-200 rounded w-32 mb-2" />
                  <div className="h-4 bg-gray-200 rounded w-48" />
                </div>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white rounded-lg p-4 h-20" />
              <div className="bg-white rounded-lg p-4 h-20" />
              <div className="bg-white rounded-lg p-4 h-20" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-3xl mx-auto px-4 py-8">
          <div data-testid="mypage-error" className="text-center py-12">
            <p className="text-gray-500 text-lg mb-4">
              프로필을 불러올 수 없습니다
            </p>
            <button
              data-testid="retry-button"
              onClick={fetchProfile}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              다시 시도
            </button>
          </div>
        </div>
      </div>
    );
  }

  const avatarLetter = (profile.display_name || profile.email)[0].toUpperCase();
  const joinDate = new Date(profile.created_at).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">마이페이지</h1>

        {/* Profile Card */}
        <div
          data-testid="profile-card"
          className="bg-white rounded-lg shadow-sm p-6 mb-6"
        >
          <div className="flex items-center gap-4">
            <div
              data-testid="profile-avatar"
              className="w-16 h-16 rounded-full bg-blue-600 flex items-center justify-center text-white text-2xl font-bold"
            >
              {avatarLetter}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <NicknameEditor
                  profile={profile}
                  onUpdate={handleNicknameUpdate}
                />
              </div>
              <p
                data-testid="profile-email"
                className="text-sm text-gray-500 mt-1"
              >
                {profile.email}
              </p>
              <p
                data-testid="profile-join-date"
                className="text-xs text-gray-400 mt-1"
              >
                {joinDate} 가입
              </p>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div
          data-testid="stats-section"
          className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6"
        >
          <div
            data-testid="stat-watchlist"
            className="bg-white rounded-lg shadow-sm p-4 text-center"
          >
            <p className="text-2xl font-bold text-gray-900">
              {profile.stats?.watchlist_count ?? 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">관심 종목</p>
          </div>
          <div
            data-testid="stat-reports"
            className="bg-white rounded-lg shadow-sm p-4 text-center"
          >
            <p className="text-2xl font-bold text-gray-900">
              {profile.stats?.report_count ?? 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">받은 리포트</p>
          </div>
          <div
            data-testid="stat-discussions"
            className="bg-white rounded-lg shadow-sm p-4 text-center"
          >
            <p className="text-2xl font-bold text-gray-900">
              {profile.stats?.discussion_count ?? 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">작성 토론</p>
          </div>
        </div>

        {/* Activity History */}
        <ActivityHistory />

        {/* Password Change Accordion */}
        <PasswordChangeForm />
      </div>
    </div>
  );
}
