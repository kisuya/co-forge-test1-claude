"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";

interface SentimentDay {
  date: string;
  avg_score: number;
  article_count: number;
}

interface SentimentTrendProps {
  stockId: string;
}

function sentimentColor(score: number): string {
  if (score > 0.2) return "#22c55e";  // green
  if (score < -0.2) return "#ef4444"; // red
  return "#9ca3af";                   // gray
}

function sentimentLabel(score: number): string {
  if (score > 0.3) return "긍정";
  if (score > 0.1) return "약간 긍정";
  if (score < -0.3) return "부정";
  if (score < -0.1) return "약간 부정";
  return "중립";
}

export default function SentimentTrend({ stockId }: SentimentTrendProps) {
  const [days, setDays] = useState<SentimentDay[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get(`/api/stocks/${stockId}/sentiment`)
      .then((resp) => {
        setDays(resp.data.days || []);
      })
      .catch(() => setError("감성 데이터를 불러오지 못했습니다"))
      .finally(() => setLoading(false));
  }, [stockId]);

  if (loading) {
    return (
      <div className="flex justify-center py-4">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error || days.length === 0) {
    return null; // Don't render section if no data
  }

  // SVG chart dimensions
  const width = 600;
  const height = 120;
  const padL = 30;
  const padR = 10;
  const padT = 10;
  const padB = 25;
  const chartW = width - padL - padR;
  const chartH = height - padT - padB;

  // Scale: x = days, y = -1 to 1
  const xStep = days.length > 1 ? chartW / (days.length - 1) : chartW;
  const yScale = (score: number) => padT + chartH / 2 - (score * chartH / 2);

  // Build polyline points
  const points = days.map((d, i) => {
    const x = padL + (days.length > 1 ? i * xStep : chartW / 2);
    const y = yScale(d.avg_score);
    return `${x},${y}`;
  }).join(" ");

  // Latest sentiment
  const latest = days[days.length - 1];

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6" data-testid="sentiment-trend">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700">뉴스 감성 트렌드</h3>
        {latest && (
          <span
            className="text-xs px-2 py-0.5 rounded-full"
            style={{
              backgroundColor: `${sentimentColor(latest.avg_score)}20`,
              color: sentimentColor(latest.avg_score),
            }}
            data-testid="sentiment-latest-badge"
          >
            최근: {sentimentLabel(latest.avg_score)}
          </span>
        )}
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full"
        data-testid="sentiment-chart"
      >
        {/* Zero line */}
        <line
          x1={padL} y1={yScale(0)} x2={width - padR} y2={yScale(0)}
          stroke="#e5e7eb" strokeWidth="1" strokeDasharray="4 2"
        />
        {/* Y labels */}
        <text x={padL - 5} y={yScale(1) + 4} fontSize="9" textAnchor="end" fill="#9ca3af">+1</text>
        <text x={padL - 5} y={yScale(0) + 3} fontSize="9" textAnchor="end" fill="#9ca3af">0</text>
        <text x={padL - 5} y={yScale(-1) + 4} fontSize="9" textAnchor="end" fill="#9ca3af">-1</text>

        {/* Area fill */}
        {days.length > 1 && (
          <polygon
            points={`${padL},${yScale(0)} ${points} ${padL + (days.length - 1) * xStep},${yScale(0)}`}
            fill="url(#sentimentGrad)"
            opacity="0.3"
          />
        )}

        {/* Gradient */}
        <defs>
          <linearGradient id="sentimentGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#22c55e" />
            <stop offset="50%" stopColor="#9ca3af" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>
        </defs>

        {/* Line */}
        {days.length > 1 ? (
          <polyline
            points={points}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
            strokeLinejoin="round"
          />
        ) : (
          <circle
            cx={padL + chartW / 2}
            cy={yScale(days[0].avg_score)}
            r="4"
            fill="#3b82f6"
          />
        )}

        {/* Dots */}
        {days.map((d, i) => {
          const x = padL + (days.length > 1 ? i * xStep : chartW / 2);
          const y = yScale(d.avg_score);
          return (
            <circle
              key={i}
              cx={x} cy={y} r="3"
              fill={sentimentColor(d.avg_score)}
              stroke="white"
              strokeWidth="1"
            />
          );
        })}

        {/* X labels (first and last date) */}
        {days.length > 0 && (
          <>
            <text x={padL} y={height - 5} fontSize="9" fill="#9ca3af" textAnchor="start">
              {days[0].date.slice(5)}
            </text>
            {days.length > 1 && (
              <text x={padL + (days.length - 1) * xStep} y={height - 5} fontSize="9" fill="#9ca3af" textAnchor="end">
                {days[days.length - 1].date.slice(5)}
              </text>
            )}
          </>
        )}
      </svg>

      <p className="text-xs text-gray-400 mt-1 text-center">
        최근 {days.length}일간 뉴스 감성 추이
      </p>
    </div>
  );
}
