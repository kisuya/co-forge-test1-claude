"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { isLoggedIn } from "@/lib/auth";

const features = [
  {
    icon: "⚡",
    title: "급변동 감지",
    description: "관심 종목의 급격한 가격 변동을 실시간으로 감지합니다.",
  },
  {
    icon: "🤖",
    title: "AI 분석",
    description: "뉴스와 공시를 분석해 변동 원인을 심층 리포트로 제공합니다.",
  },
  {
    icon: "📊",
    title: "이벤트 히스토리",
    description: "과거 이벤트와 가격 변동 패턴을 한눈에 확인할 수 있습니다.",
  },
];

export default function LandingPage() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (isLoggedIn()) {
      router.push("/dashboard");
    } else {
      setChecking(false);
    }
  }, [router]);

  if (checking) {
    return (
      <main data-testid="landing-skeleton" className="flex min-h-screen items-center justify-center">
        <div className="animate-pulse w-full max-w-2xl space-y-6 px-4">
          <div className="h-10 bg-gray-200 rounded w-3/4 mx-auto" />
          <div className="h-6 bg-gray-200 rounded w-1/2 mx-auto" />
          <div className="h-12 bg-gray-200 rounded w-40 mx-auto" />
        </div>
      </main>
    );
  }

  return (
    <main data-testid="landing-page" className="min-h-screen">
      {/* Hero section */}
      <section
        data-testid="hero-section"
        className="flex flex-col items-center justify-center text-center py-24 px-4"
      >
        <h1
          data-testid="hero-title"
          className="text-3xl md:text-4xl font-bold text-gray-900 max-w-2xl"
          style={{ fontSize: "clamp(28px, 4vw, 36px)" }}
        >
          주가가 급변했을 때, AI가 이유를 알려드립니다
        </h1>
        <p
          data-testid="hero-subtitle"
          className="mt-4 text-base text-gray-500 max-w-xl"
        >
          뉴스와 공시를 분석해 변동 원인을 심층 리포트로 제공합니다
        </p>
        <Link
          href="/signup"
          data-testid="hero-cta"
          className="mt-8 px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
        >
          무료로 시작하기
        </Link>
      </section>

      {/* Feature cards */}
      <section
        data-testid="features-section"
        className="max-w-5xl mx-auto px-4 pb-24"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((feature) => (
            <div
              key={feature.title}
              data-testid="feature-card"
              className="bg-white rounded-lg p-6 shadow-sm border border-gray-100 text-center"
            >
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-gray-500">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Bottom CTA */}
      <section
        data-testid="bottom-cta-section"
        className="text-center py-16 bg-gray-100"
      >
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          지금 바로 시작하세요
        </h2>
        <Link
          href="/signup"
          data-testid="bottom-cta"
          className="inline-block px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
        >
          무료로 시작하기
        </Link>
      </section>
    </main>
  );
}
