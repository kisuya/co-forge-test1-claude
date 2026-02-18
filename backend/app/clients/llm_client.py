from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.config import get_settings


@dataclass
class AnalysisCause:
    """A single cause identified by the LLM."""
    reason: str
    confidence: str  # "high", "medium", "low"
    impact: str


@dataclass
class MultiLayerCause:
    """A cause with impact_level for multi-layer analysis."""
    reason: str
    confidence: str  # "high", "medium", "low"
    impact: str
    impact_level: str = "significant"  # "critical", "significant", "minor"


@dataclass
class OutlookResult:
    """Short-term or medium-term outlook."""
    summary: str = ""
    sentiment: str = "neutral"  # "bullish", "bearish", "neutral"
    catalysts: list[str] = field(default_factory=list)


@dataclass
class MultiLayerAnalysisResult:
    """Structured result from multi-layer LLM analysis."""
    summary: str
    direct_causes: list[MultiLayerCause] = field(default_factory=list)
    indirect_causes: list[MultiLayerCause] = field(default_factory=list)
    macro_factors: list[MultiLayerCause] = field(default_factory=list)
    short_term_outlook: OutlookResult | None = None
    medium_term_outlook: OutlookResult | None = None
    raw_response: str = ""

    @property
    def causes(self) -> list[AnalysisCause]:
        """Backward-compatible flat causes list."""
        all_causes: list[AnalysisCause] = []
        for c in self.direct_causes + self.indirect_causes + self.macro_factors:
            all_causes.append(AnalysisCause(
                reason=c.reason,
                confidence=c.confidence,
                impact=c.impact,
            ))
        return all_causes


# Keep AnalysisResult for backward compatibility
@dataclass
class AnalysisResult:
    """Structured result from LLM analysis."""
    summary: str
    causes: list[AnalysisCause] = field(default_factory=list)
    raw_response: str = ""


def _parse_cause_list(items: list) -> list[MultiLayerCause]:
    """Parse a list of cause dicts into MultiLayerCause objects."""
    result = []
    for c in items:
        if not isinstance(c, dict):
            continue
        result.append(MultiLayerCause(
            reason=c.get("reason", ""),
            confidence=c.get("confidence", "medium"),
            impact=c.get("impact", ""),
            impact_level=c.get("impact_level", "significant"),
        ))
    return result


def _parse_outlook(data: dict | None) -> OutlookResult | None:
    """Parse an outlook dict into OutlookResult."""
    if not data or not isinstance(data, dict):
        return None
    summary = data.get("summary", "")
    if not summary:
        return None
    sentiment = data.get("sentiment", "neutral")
    if sentiment not in ("bullish", "bearish", "neutral"):
        sentiment = "neutral"
    catalysts = data.get("catalysts", [])
    if not isinstance(catalysts, list):
        catalysts = []
    catalysts = [str(c) for c in catalysts if c]
    return OutlookResult(summary=summary, sentiment=sentiment, catalysts=catalysts)


def build_multilayer_prompt(
    stock_name: str,
    stock_code: str,
    change_pct: float,
    source_text: str,
) -> str:
    """Build the multi-layer analysis prompt."""
    return f"""주식 변동에 대한 다층 원인 분석을 요청합니다.

종목: {stock_name} ({stock_code})
변동률: {change_pct:+.1f}%

관련 뉴스/공시:
{source_text}

다음 3단계로 원인을 분류하여 분석해주세요:

1. **직접 원인 (Direct)**: 해당 종목에 직접 영향을 미치는 요인
   - 실적 발표, 수주, 규제 변경, 경영진 변동, 자사주 매입 등
2. **간접 원인 (Indirect)**: 관련 산업/공급망을 통해 간접 영향
   - 부품/원자재 가격 변동, 경쟁사 실적, 산업 트렌드, 고객사 동향 등
3. **시장 환경 (Macro)**: 거시경제/시장 전체 요인
   - 금리, 환율, 지정학 리스크, 글로벌 증시 흐름, 정책 변화 등

각 원인에 다음 정보를 포함해주세요:
- reason: 원인 설명
- confidence: 확신도 (high/medium/low)
- impact: 영향 설명
- impact_level: 영향 수준 (critical/significant/minor)

또한 전망(outlook)도 제시해주세요:
- short_term: 1주 이내 전망 (summary 2-3줄, sentiment: bullish/bearish/neutral, catalysts: 주요 촉매 요인 리스트)
- medium_term: 1개월 전망 (summary 2-3줄, sentiment: bullish/bearish/neutral, catalysts: 주요 촉매 요인 리스트)

JSON으로 응답해주세요:
{{"summary": "변동 요약 (1줄)", "direct_causes": [{{"reason": "...", "confidence": "high|medium|low", "impact": "...", "impact_level": "critical|significant|minor"}}], "indirect_causes": [...], "macro_factors": [...], "short_term": {{"summary": "1주 전망 2-3줄", "sentiment": "bullish|bearish|neutral", "catalysts": ["촉매1", "촉매2"]}}, "medium_term": {{"summary": "1개월 전망 2-3줄", "sentiment": "bullish|bearish|neutral", "catalysts": ["촉매1", "촉매2"]}}}}

규칙:
- 각 카테고리에 0~3개의 원인을 제시
- 해당 카테고리에 원인이 없으면 빈 배열 []
- 한국어로 작성
- JSON만 출력 (설명 텍스트 없이)"""


def parse_multilayer_response(raw: str) -> MultiLayerAnalysisResult:
    """Parse LLM response into MultiLayerAnalysisResult."""
    try:
        parsed = json.loads(raw)
        return MultiLayerAnalysisResult(
            summary=parsed.get("summary", ""),
            direct_causes=_parse_cause_list(parsed.get("direct_causes", [])),
            indirect_causes=_parse_cause_list(parsed.get("indirect_causes", [])),
            macro_factors=_parse_cause_list(parsed.get("macro_factors", [])),
            short_term_outlook=_parse_outlook(parsed.get("short_term")),
            medium_term_outlook=_parse_outlook(parsed.get("medium_term")),
            raw_response=raw,
        )
    except json.JSONDecodeError:
        return MultiLayerAnalysisResult(summary=raw[:200], raw_response=raw)


def analyze_stock_movement(
    stock_name: str,
    stock_code: str,
    change_pct: float,
    sources: list[dict[str, str]],
) -> MultiLayerAnalysisResult:
    """Send multi-layer analysis prompt to Claude API and parse structured result.

    Returns MultiLayerAnalysisResult with backward-compatible .causes property.
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        return MultiLayerAnalysisResult(
            summary="API key not configured",
        )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        source_text = "\n".join(
            f"- [{s.get('type', 'unknown')}] {s.get('title', '')} ({s.get('url', '')})"
            for s in sources
        )

        prompt = build_multilayer_prompt(
            stock_name, stock_code, change_pct, source_text,
        )

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text
        return parse_multilayer_response(raw)

    except Exception as e:
        return MultiLayerAnalysisResult(summary=f"Analysis failed: {e}")
