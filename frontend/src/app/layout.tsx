import type { Metadata } from "next";
import "./globals.css";
import ToastContainer from "@/components/ToastContainer";
import ProgressBar from "@/components/ProgressBar";

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
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        <ProgressBar />
        <ToastContainer />
        {children}
      </body>
    </html>
  );
}
