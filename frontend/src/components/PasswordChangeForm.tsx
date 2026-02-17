"use client";

import { useState } from "react";
import { profileApi } from "@/lib/queries";
import { addToast } from "@/lib/toast";

export default function PasswordChangeForm() {
  const [open, setOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mismatch = confirmPassword.length > 0 && newPassword !== confirmPassword;

  const resetForm = () => {
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setShowCurrent(false);
    setShowNew(false);
    setShowConfirm(false);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (mismatch) return;
    setSaving(true);
    setError(null);
    try {
      await profileApi.changePassword(currentPassword, newPassword);
      addToast("비밀번호가 변경되었습니다", "success");
      resetForm();
      setOpen(false);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { message?: string } } };
      if (axiosErr.response?.status === 400) {
        setError("현재 비밀번호가 올바르지 않습니다");
      } else if (axiosErr.response?.status === 422) {
        setError("비밀번호는 8자 이상, 영문과 숫자를 포함해야 합니다");
      } else {
        setError("비밀번호 변경에 실패했습니다");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div data-testid="password-change-section" className="bg-white rounded-lg shadow-sm mb-6">
      <button
        data-testid="password-toggle"
        onClick={() => setOpen(!open)}
        className="w-full px-6 py-4 flex items-center justify-between text-left"
      >
        <span className="font-medium text-gray-900">비밀번호 변경</span>
        <span className="text-gray-400">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <form
          data-testid="password-form"
          onSubmit={handleSubmit}
          className="px-6 pb-6 space-y-4"
        >
          <div>
            <label className="block text-sm text-gray-700 mb-1">현재 비밀번호</label>
            <div className="relative">
              <input
                data-testid="current-password-input"
                type={showCurrent ? "text" : "password"}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 pr-10 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                required
              />
              <button
                type="button"
                data-testid="toggle-current-visibility"
                onClick={() => setShowCurrent(!showCurrent)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400"
              >
                👁
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">새 비밀번호</label>
            <div className="relative">
              <input
                data-testid="new-password-input"
                type={showNew ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 pr-10 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                required
              />
              <button
                type="button"
                data-testid="toggle-new-visibility"
                onClick={() => setShowNew(!showNew)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400"
              >
                👁
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">새 비밀번호 확인</label>
            <div className="relative">
              <input
                data-testid="confirm-password-input"
                type={showConfirm ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 pr-10 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                required
              />
              <button
                type="button"
                data-testid="toggle-confirm-visibility"
                onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400"
              >
                👁
              </button>
            </div>
            {mismatch && (
              <p data-testid="password-mismatch" className="text-red-500 text-xs mt-1">
                비밀번호가 일치하지 않습니다
              </p>
            )}
          </div>
          {error && (
            <p data-testid="password-error" className="text-red-500 text-sm">
              {error}
            </p>
          )}
          <button
            data-testid="password-submit-btn"
            type="submit"
            disabled={saving || mismatch || !currentPassword || !newPassword || !confirmPassword}
            className="w-full py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "변경 중..." : "비밀번호 변경"}
          </button>
        </form>
      )}
    </div>
  );
}
