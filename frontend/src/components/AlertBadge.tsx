"use client";

interface AlertBadgeProps {
  changePct: number;
  size?: "sm" | "md";
}

export default function AlertBadge({
  changePct,
  size = "sm",
}: AlertBadgeProps) {
  const isPositive = changePct > 0;
  const isSpike = Math.abs(changePct) >= 3;

  const sizeClass = size === "md" ? "px-3 py-1 text-sm" : "px-2 py-0.5 text-xs";

  let colorClass: string;
  if (isSpike && isPositive) {
    colorClass = "bg-red-100 text-red-800 border border-red-200";
  } else if (isSpike && !isPositive) {
    colorClass = "bg-blue-100 text-blue-800 border border-blue-200";
  } else if (isPositive) {
    colorClass = "bg-red-50 text-red-600";
  } else {
    colorClass = "bg-blue-50 text-blue-600";
  }

  const sign = isPositive ? "+" : "";

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full ${sizeClass} ${colorClass}`}
      data-testid="alert-badge"
    >
      {sign}{changePct.toFixed(2)}%
      {isSpike && " ⚠"}
    </span>
  );
}
