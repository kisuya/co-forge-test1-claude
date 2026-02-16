import axios from "axios";
import { addToast } from "@/lib/toast";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (axios.isCancel(error)) return Promise.reject(error);

    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const resp = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token } = resp.data;
          localStorage.setItem("access_token", access_token);
          localStorage.setItem("refresh_token", refresh_token);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          if (typeof window !== "undefined") {
            addToast("세션이 만료되었습니다. 다시 로그인해주세요.");
            window.location.href = "/login";
          }
          return Promise.reject(error);
        }
      }
    }

    if (!error.response) {
      addToast("네트워크 연결을 확인해주세요.");
    } else if (error.response.status >= 500) {
      addToast("서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
    }

    return Promise.reject(error);
  }
);

export interface SignupRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
}

export interface SignupResponse {
  id: string;
  email: string;
}

export const authApi = {
  signup: (data: SignupRequest) => api.post<SignupResponse>("/api/auth/signup", data),
  login: (data: LoginRequest) => api.post<TokenResponse>("/api/auth/login", data),
  refresh: (refreshToken: string) =>
    api.post<TokenResponse>("/api/auth/refresh", { refresh_token: refreshToken }),
};

export default api;
