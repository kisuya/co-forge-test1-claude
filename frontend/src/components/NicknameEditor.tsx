"use client";

import { useState, useRef, useEffect } from "react";
import { profileApi } from "@/lib/queries";
import { addToast } from "@/lib/toast";
import type { ProfileResponse } from "@/types";

interface NicknameEditorProps {
  profile: ProfileResponse;
  onUpdate: (updated: ProfileResponse) => void;
}

export default function NicknameEditor({
  profile,
  onUpdate,
}: NicknameEditorProps) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(profile.display_name);
  const [saving, setSaving] = useState(false);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  const startEdit = () => {
    setValue(profile.nickname || profile.display_name);
    setFieldError(null);
    setEditing(true);
  };

  const cancel = () => {
    setValue(profile.display_name);
    setFieldError(null);
    setEditing(false);
  };

  const save = async () => {
    const trimmed = value.trim();
    if (!trimmed) {
      setFieldError("2~20자, 한글/영문/숫자만 가능");
      return;
    }
    setSaving(true);
    setFieldError(null);
    try {
      const res = await profileApi.updateNickname(trimmed);
      onUpdate(res.data);
      addToast("닉네임이 변경되었습니다", "success");
      setEditing(false);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { message?: string } } };
      if (axiosErr.response?.status === 409) {
        addToast("이미 사용 중인 닉네임입니다", "error");
      } else if (axiosErr.response?.status === 422) {
        setFieldError("2~20자, 한글/영문/숫자만 가능");
      } else {
        addToast("닉네임 변경에 실패했습니다", "error");
      }
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      save();
    } else if (e.key === "Escape") {
      cancel();
    }
  };

  if (editing) {
    return (
      <div data-testid="nickname-edit-mode">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            data-testid="nickname-input"
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            maxLength={20}
            className="text-xl font-bold text-gray-900 border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          />
          <button
            data-testid="nickname-save-btn"
            onClick={save}
            disabled={saving}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "..." : "저장"}
          </button>
          <button
            data-testid="nickname-cancel-btn"
            onClick={cancel}
            className="px-3 py-1 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            취소
          </button>
        </div>
        {fieldError && (
          <p data-testid="nickname-field-error" className="text-red-500 text-xs mt-1">
            {fieldError}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2" data-testid="nickname-display">
      <span data-testid="profile-nickname" className="text-xl font-bold text-gray-900">
        {profile.display_name}
      </span>
      <button
        data-testid="nickname-edit-btn"
        onClick={startEdit}
        className="text-gray-400 hover:text-gray-600"
        aria-label="닉네임 수정"
      >
        ✏️
      </button>
    </div>
  );
}
