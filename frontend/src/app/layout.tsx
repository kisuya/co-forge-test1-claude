import type { Metadata } from "next";
import "./globals.css";
import ToastContainer from "@/components/ToastContainer";
import ProgressBar from "@/components/ProgressBar";
import GlobalHeader from "@/components/GlobalHeader";
import GlobalFooter from "@/components/GlobalFooter";
import MobileNav from "@/components/MobileNav";

export const metadata: Metadata = {
  title: {
    default: "oh-my-stock | AI 주가 변동 분석",
    template: "%s | oh-my-stock",
  },
  description: "관심 종목의 주가가 급변했을 때 AI가 원인을 분석합니다",
  openGraph: {
    title: "oh-my-stock | AI 주가 변동 분석",
    description: "관심 종목의 주가가 급변했을 때 AI가 원인을 분석합니다",
    siteName: "oh-my-stock",
    type: "website",
    images: ["/og-image.png"],
  },
  twitter: {
    card: "summary_large_image",
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#2563EB" />
      </head>
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased pb-14 md:pb-0">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[100] focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-md focus:outline-2 focus:outline-blue-600"
          data-testid="skip-to-main"
        >
          본문으로 건너뛰기
        </a>
        <ProgressBar />
        <ToastContainer />
        <GlobalHeader />
        <main id="main-content">{children}</main>
        <GlobalFooter />
        <MobileNav />
      </body>
    </html>
  );
}
