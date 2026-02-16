import type { Metadata } from "next";
import "./globals.css";

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
        {children}
      </body>
    </html>
  );
}
