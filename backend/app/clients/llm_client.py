from __future__ import annotations

from dataclasses import dataclass, field

from app.config import get_settings


@dataclass
class AnalysisCause:
    """A single cause identified by the LLM."""
    reason: str
    confidence: str  # "high", "medium", "low"
    impact: str


@dataclass
class AnalysisResult:
    """Structured result from LLM analysis."""
    summary: str
    causes: list[AnalysisCause] = field(default_factory=list)
    raw_response: str = ""


def analyze_stock_movement(
    stock_name: str,
    stock_code: str,
    change_pct: float,
    sources: list[dict[str, str]],
) -> AnalysisResult:
    """Send analysis prompt to Claude API and parse structured result.

    In production, calls Anthropic Claude API.
    For testing, this function is mocked.
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        return AnalysisResult(
            summary="API key not configured",
            causes=[],
        )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        source_text = "\n".join(
            f"- [{s.get('type', 'unknown')}] {s.get('title', '')} ({s.get('url', '')})"
            for s in sources
        )

        prompt = f"""주식 변동 분석을 요청합니다.

종목: {stock_name} ({stock_code})
변동률: {change_pct:+.1f}%

관련 뉴스/공시:
{source_text}

다음 형식으로 분석해주세요:
1. 변동 요약 (1줄)
2. 주요 원인 (1-3개, 각각 확신도: high/medium/low)
3. 영향 분석

JSON으로 응답해주세요:
{{"summary": "...", "causes": [{{"reason": "...", "confidence": "high|medium|low", "impact": "..."}}]}}"""

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text
        import json
        try:
            parsed = json.loads(raw)
            return AnalysisResult(
                summary=parsed.get("summary", ""),
                causes=[
                    AnalysisCause(
                        reason=c.get("reason", ""),
                        confidence=c.get("confidence", "medium"),
                        impact=c.get("impact", ""),
                    )
                    for c in parsed.get("causes", [])
                ],
                raw_response=raw,
            )
        except json.JSONDecodeError:
            return AnalysisResult(summary=raw[:200], raw_response=raw)

    except Exception as e:
        return AnalysisResult(summary=f"Analysis failed: {e}")
