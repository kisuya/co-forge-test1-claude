"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { usePathname } from "next/navigation";

export default function ProgressBar() {
  const pathname = usePathname();
  const [progress, setProgress] = useState(0);
  const [visible, setVisible] = useState(false);
  const prevPath = useRef(pathname);

  const start = useCallback(() => {
    setProgress(20);
    setVisible(true);
  }, []);

  const done = useCallback(() => {
    setProgress(100);
    setTimeout(() => {
      setVisible(false);
      setProgress(0);
    }, 300);
  }, []);

  useEffect(() => {
    if (pathname !== prevPath.current) {
      start();
      const id = setTimeout(done, 150);
      prevPath.current = pathname;
      return () => clearTimeout(id);
    }
  }, [pathname, start, done]);

  useEffect(() => {
    if (visible && progress < 90) {
      const id = setTimeout(() => setProgress((p) => p + (90 - p) * 0.1), 200);
      return () => clearTimeout(id);
    }
  }, [visible, progress]);

  if (!visible) return null;

  return (
    <div
      className="fixed top-0 left-0 right-0 h-0.5 z-50 bg-transparent"
      data-testid="progress-bar"
    >
      <div
        className="h-full bg-blue-600 transition-all duration-300 ease-out"
        style={{ width: `${progress}%` }}
      />
    </div>
  );
}
