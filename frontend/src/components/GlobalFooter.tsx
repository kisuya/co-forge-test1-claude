"use client";

import { usePathname } from "next/navigation";

export default function GlobalFooter() {
  const pathname = usePathname();

  // Hide on shared pages
  const isSharedPage = pathname?.startsWith("/shared");
  if (isSharedPage) return null;

  return (
    <footer
      data-testid="global-footer"
      className="bg-gray-50 border-t border-gray-200 mb-14 md:mb-0"
      style={{ padding: "24px" }}
    >
      <div className="max-w-7xl mx-auto text-center space-y-3">
        {/* Disclaimer */}
        <p
          data-testid="footer-disclaimer"
          className="text-xs text-gray-500"
        >
          본 서비스는 투자 조언을 제공하지 않습니다. 투자 판단의 책임은 본인에게 있습니다.
        </p>

        {/* Links */}
        <div
          data-testid="footer-links"
          className="flex items-center justify-center gap-4"
        >
          <a
            href="#"
            data-testid="footer-terms"
            className="text-xs text-gray-500 hover:underline"
          >
            이용약관
          </a>
          <span className="text-gray-300">|</span>
          <a
            href="#"
            data-testid="footer-privacy"
            className="text-xs text-gray-500 hover:underline"
          >
            개인정보처리방침
          </a>
          <span className="text-gray-300">|</span>
          <a
            href="#"
            data-testid="footer-contact"
            className="text-xs text-gray-500 hover:underline"
          >
            문의
          </a>
        </div>

        {/* Copyright */}
        <p
          data-testid="footer-copyright"
          className="text-xs text-gray-500"
        >
          © 2026 oh-my-stock
        </p>
      </div>
    </footer>
  );
}
