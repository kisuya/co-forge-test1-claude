"use client";

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  rounded?: boolean;
  className?: string;
}

export default function Skeleton({
  width,
  height,
  rounded = false,
  className = "",
}: SkeletonProps) {
  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === "number" ? `${width}px` : width;
  if (height) style.height = typeof height === "number" ? `${height}px` : height;

  return (
    <div
      data-testid="skeleton"
      className={`bg-gray-200 animate-pulse ${rounded ? "rounded-full" : "rounded"} ${className}`}
      style={style}
    />
  );
}
