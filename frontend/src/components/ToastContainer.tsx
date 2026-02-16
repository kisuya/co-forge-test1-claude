"use client";

import { useState, useEffect } from "react";
import { subscribe, removeToast, type ToastMessage, type ToastType } from "@/lib/toast";

const BG: Record<ToastType, string> = {
  error: "bg-red-600",
  success: "bg-green-600",
  info: "bg-blue-600",
};

export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => subscribe(setToasts), []);

  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed top-4 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 w-full max-w-sm px-4"
      data-testid="toast-container"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`${BG[t.type]} text-white px-4 py-3 rounded-lg shadow-lg flex items-center justify-between text-sm animate-slide-down`}
          role="alert"
          data-testid="toast-message"
        >
          <span>{t.text}</span>
          <button
            onClick={() => removeToast(t.id)}
            className="ml-3 text-white/80 hover:text-white"
            aria-label="닫기"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
