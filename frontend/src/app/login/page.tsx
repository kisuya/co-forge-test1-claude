"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api";
import { setTokens } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setFieldErrors({});
    setLoading(true);

    try {
      const resp = await authApi.login({ email, password });
      setTokens(resp.data.access_token, resp.data.refresh_token);
      if (resp.data.is_first_login) {
        localStorage.setItem("onboarding_pending", "true");
      }
      router.push("/dashboard");
    } catch {
      setError("이메일 또는 비밀번호가 올바르지 않습니다");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      data-testid="login-page"
      className="flex min-h-screen items-center justify-center px-4"
    >
      <div
        data-testid="auth-card"
        className="w-full bg-white shadow-md p-8"
        style={{ maxWidth: "400px", borderRadius: "var(--radius-md, 8px)" }}
      >
        {/* Logo + Title */}
        <div className="text-center mb-6">
          <h1
            data-testid="auth-logo"
            className="text-2xl font-bold text-gray-900"
          >
            oh-my-stock
          </h1>
          <h2
            data-testid="auth-title"
            className="mt-2 text-lg font-semibold text-gray-700"
          >
            로그인
          </h2>
        </div>

        <form
          data-testid="login-form"
          onSubmit={handleSubmit}
          className="space-y-4"
        >
          {error && (
            <div
              data-testid="auth-error"
              className="rounded-md bg-red-50 p-3 text-sm text-red-600"
            >
              {error}
            </div>
          )}

          <div>
            <label
              htmlFor="email"
              data-testid="label-email"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              이메일
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              data-testid="input-email"
              className={`block w-full border px-3 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                fieldErrors.email
                  ? "border-red-500"
                  : "border-gray-300"
              }`}
              style={{
                borderRadius: "var(--radius-md, 8px)",
                padding: "12px",
                height: "48px",
              }}
              placeholder="you@example.com"
              aria-describedby={fieldErrors.email ? "login-email-error" : undefined}
            />
            {fieldErrors.email && (
              <p
                id="login-email-error"
                data-testid="field-error-email"
                className="mt-1 text-xs text-red-500"
              >
                {fieldErrors.email}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="password"
              data-testid="label-password"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              비밀번호
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              data-testid="input-password"
              className={`block w-full border px-3 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                fieldErrors.password
                  ? "border-red-500"
                  : "border-gray-300"
              }`}
              style={{
                borderRadius: "var(--radius-md, 8px)",
                padding: "12px",
                height: "48px",
              }}
              aria-describedby={fieldErrors.password ? "login-password-error" : undefined}
            />
            {fieldErrors.password && (
              <p
                id="login-password-error"
                data-testid="field-error-password"
                className="mt-1 text-xs text-red-500"
              >
                {fieldErrors.password}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            data-testid="auth-submit-btn"
            className="w-full bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
            style={{
              borderRadius: "var(--radius-md, 8px)",
              height: "48px",
            }}
          >
            {loading ? "로그인 중..." : "로그인"}
          </button>
        </form>

        <p
          data-testid="auth-switch-link"
          className="mt-6 text-center text-sm text-gray-600"
        >
          계정이 없으신가요?{" "}
          <Link href="/signup" className="text-blue-600 hover:underline">
            회원가입
          </Link>
        </p>
      </div>
    </main>
  );
}
