# Market Research: StockWhy (주가 변동 원인 분석 서비스)

## Target User Profile

### 핵심 타겟

- **누구**: 1년 이상 주식 투자 경험이 있는 한국 개인투자자
- **연령**: 30-50대 (투자 경험 + 디지털 리터러시 겸비)
- **투자 규모**: 1,000만 원 ~ 5억 원 포트폴리오
- **행동 패턴**: 매일 증권 앱 확인, 주 2-3회 관련 뉴스 검색
- **핵심 니즈**: "오늘 내 종목이 왜 빠졌지?" → 직접 뉴스 찾아보기 귀찮거나 시간 부족
- **증권사**: 2개 이상 계좌 보유 (토스, 키움, 한투 등 분산)

### 사용자 시나리오

> "오전에 출근했는데 삼성전자가 3% 빠졌어. 점심시간에 왜 빠졌는지 찾아보려고 뉴스를 검색했는데 기사가 너무 많고 뭐가 핵심인지 모르겠어. 예전에 비슷한 일이 있었을 때 어떻게 됐는지도 궁금해."

### 사용자가 아닌 사람

- 단타/스캘핑 트레이더 (실시간 속도가 중요, 이 서비스는 깊이 중심)
- 투자 초보자 (심층 분석보다 기초 교육이 필요)
- 기관 투자자 (자체 리서치 팀 보유)

## Market Size Estimation

### Bottom-Up 추정

| 단계 | 수치 | 근거 |
|------|------|------|
| 한국 개인투자자 수 | 1,423만 명 | 한국예탁결제원 2024년 12월 기준 |
| 1년 이상 경험자 비율 | 50% | 2020년 이후 유입자 중 잔존율 추정 |
| 경험 있는 투자자 | ~710만 명 | |
| "원인 분석" 니즈 보유 비율 | 10% | 능동적으로 변동 원인을 찾는 사용자 |
| 잠재 TAM (한국) | ~71만 명 | |
| 독립 유료 서비스 전환율 | 2% | 신규 핀테크 서비스 보수적 추정 |
| **SOM (한국)** | **~14,000명** | |
| 월 구독 단가 | 9,900원 | |
| **연간 매출 (한국 SOM)** | **~16.6억 원** | |

### 확장 시나리오

- **미국 시장 확장**: 한국인 미국 주식 투자자 약 400만 명 (해외주식 거래 급증), 추가 SOM 5,000-10,000명
- **글로벌 영문 서비스**: TAM 수십배 확장 가능하나 경쟁도 격화
- **B2B (증권사/핀테크 파트너십)**: 분석 엔진을 API로 제공 → 별도 수익 채널

## Competitive Analysis

### 비교 테이블

| 항목 | **StockWhy (우리)** | **토스 AI 시그널** | **Market Mover (Ainvest)** | **씽크풀** | **Seeking Alpha** |
|------|---------------------|-------------------|---------------------------|-----------|-------------------|
| **핵심 기능** | 주가 변동 심층 원인 분석 | 변동 원인 요약 | 변동 이유 카드 | AI 주가 예측 | 뉴스 + 애널리스트 분석 |
| **분석 깊이** | 유사 케이스 + 장기 트렌드 | 핵심 요약 1-2줄 | 간단한 이유 제시 | 시세 기반 예측 | 상세 (사람 작성) |
| **한국 주식** | O | O | X | O | X |
| **미국 주식** | O | 제한적 | O | X | O |
| **플랫폼** | 웹 (독립) | 토스증권 MTS | iOS 앱 | 웹/앱 | 웹/앱 |
| **증권사 종속** | 없음 | 토스증권 필수 | 없음 | 없음 | 없음 |
| **가격** | 프리미엄 (예: 9,900원/월) | 무료 | 무료 (인앱 구매) | 무료/유료 | $239/년 (~3만원/월) |
| **언어** | 한국어 | 한국어 | 영어 | 한국어 | 영어 |

### 경쟁 우위 분석

**우리만의 포지션: "증권사 무관 + 한미 통합 + 심층 분석"**

이 세 가지를 동시에 제공하는 서비스는 현재 존재하지 않음:
- 토스: 심층 분석 X, 증권사 종속
- Ainvest: 한국 X, 심층 분석 X
- 씽크풀: 미국 X, 원인 분석 아님
- Seeking Alpha: 한국어 X, 고가

### 경쟁 리스크

- **단기 (6개월)**: 토스가 분석 깊이를 강화할 가능성. 다만 증권사 종속은 구조적 한계
- **중기 (1년)**: 다른 증권사 (키움, 한투)도 유사 AI 기능 탑재 예상. 독립 서비스의 "통합" 가치가 오히려 상승
- **장기 (2년+)**: 네이버/카카오 등 플랫폼 기업 진입 가능성. 분석 품질과 커뮤니티로 방어

## Market Trends

### 성장 요인

1. **한국 투자 인구 안정화**: 1,400만 명 이상 유지. 2020년 급증 후 정착 단계
2. **해외 주식 투자 급증**: 한국인 미국 주식 직접투자 규모 지속 증가
3. **AI 비용 하락**: LLM API 비용이 매년 50% 이상 하락 → 서비스 운영 비용 개선
4. **정보 과잉 시대**: 뉴스/정보는 넘치지만 "왜?"에 대한 답을 주는 서비스는 부족
5. **글로벌 주식 거래 앱 시장**: $24.1B (2022) → 19% CAGR 성장 중

### 우려 요인

1. **20-40대 투자자 감소 추세**: 2022년 이후 MZ세대 이탈 심각 — 핵심 디지털 타겟이 줄고 있음
2. **무료 서비스 기대**: 증권사가 무료로 제공하는 기능에 돈을 낼 것인가?
3. **규제 리스크**: 투자 조언으로 간주될 경우 금융 관련 규제 적용 가능

## Opportunities

### 1. 증권사 통합 포트폴리오 분석
여러 증권사에 분산된 포트폴리오를 한곳에서 모니터링 → "왜 내 전체 자산이 변동했는지" 통합 분석. 증권사 종속 서비스는 구조적으로 불가능한 기능.

### 2. 과거 케이스 DB (유사 사례 분석)
"삼성전자가 실적 미스로 3% 빠진 과거 5번의 사례에서, 이후 1개월간 평균 +2.1% 반등"
→ 이런 수준의 분석은 토스 AI 시그널이 제공하지 않는 고유 가치.

### 3. B2B API 서비스
분석 엔진을 API로 제공 → 중소형 증권사/핀테크가 자체 서비스에 통합. 수익 다변화.

### 4. 커뮤니티 기능
같은 종목을 보유한 투자자 간 토론 → 네트워크 효과로 사용자 고착도 증가.

## Sources

### 한국 시장 데이터
- [한국예탁결제원 투자자 통계](http://mhdata.or.kr/mailing/Numbers310_251111_B1_Part.pdf)
- [한국인의 주식투자 실태](http://www.mhdata.or.kr/bbs/board.php?bo_table=society&wr_id=583)
- [MZ세대 투자자 이탈 분석 (Investing.com)](https://kr.investing.com/analysis/article-200447152)

### 경쟁사 분석
- [토스증권 AI 시그널 출시 (머니투데이)](https://www.mt.co.kr/stock/2025/11/12/2025111216254521519)
- [토스증권 AI 시그널 (한국경제)](https://www.hankyung.com/article/2025111289706)
- [씽크풀 AI 챗봇 (뉴스핌)](https://www.newspim.com/news/view/20240518000064)
- [Market Mover: Reason & Insight (App Store)](https://apps.apple.com/us/app/market-mover-reason-insight/id6472856176)
- [Danelfin AI Stock Picker](https://danelfin.com/)
- [Seeking Alpha On the Move](https://seekingalpha.com/market-news/on-the-move)

### 기술 데이터 소스
- [DART OpenAPI (전자공시시스템)](https://opendart.fss.or.kr/intro/main.do)
- [KRX Open API (한국거래소)](https://openapi.krx.co.kr/)
- [PyKRX (GitHub)](https://github.com/sharebook-kr/pykrx)
- [Alpha Vantage](https://www.alphavantage.co/)
- [Finnhub](https://finnhub.io/)
- [EODHD Financial News API](https://eodhd.com/financial-apis/stock-market-financial-news-api)

### 시장 규모
- [주식 거래 앱 시장 규모 보고서 (GMInsights)](https://www.gminsights.com/industry-analysis/stock-trading-and-investing-applications-market)
- [AI Stock Analysis Tools 2026 (Wall Street Zen)](https://www.wallstreetzen.com/blog/ai-stock-analysis/)
- [Best Stock Alert Services 2025 (Benzinga)](https://www.benzinga.com/money/best-stock-alerts-services)
