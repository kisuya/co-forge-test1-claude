import type { Metadata } from "next";
import "./globals.css";
import ToastContainer from "@/components/ToastContainer";
import ProgressBar from "@/components/ProgressBar";
import GlobalHeader from "@/components/GlobalHeader";
import GlobalFooter from "@/components/GlobalFooter";
import MobileNav from "@/components/MobileNav";

export const metadata: Metadata = {
  title: "oh-my-stock",
  description: "AI-powered stock movement analysis",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased pb-14 md:pb-0">
        <ProgressBar />
        <ToastContainer />
        <GlobalHeader />
        {children}
        <GlobalFooter />
        <MobileNav />
      </body>
    </html>
  );
}
