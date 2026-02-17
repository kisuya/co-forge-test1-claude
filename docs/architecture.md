# Architecture: oh-my-stock

## System Type

모놀리식 아키텍처 (MVP). 백엔드(Python/FastAPI)와 프론트엔드(Next.js)를 분리하되, 단일 저장소에서 관리.

```
[Browser] → [Next.js Frontend] → [FastAPI Backend] → [PostgreSQL]
                                        ↓
                                  [Background Workers]
                                   ├── 한국 주가 수집기 (PyKRX)
                                   ├── 미국 주가 수집기 (yfinance)
                                   ├── 뉴스/공시 수집기 (한국 + 영문)
                                   ├── AI 분석 엔진 + 유사 케이스 매칭
                                   └── 푸시 발송 워커 (Web Push)
```

## Tech Stack

| 계층 | 선택 | 이유 |
|------|------|------|
| Backend | Python 3.12 + FastAPI | 금융 데이터 라이브러리 풍부, AI 생태계 최강 |
| Frontend | Next.js 15 (App Router) + TypeScript | SSR 지원, React 생태계, 빠른 개발 |
| Database | PostgreSQL 16 | 구조화된 데이터(종목, 리포트, 사용자), 안정적 |
| Cache | Redis | 주가 데이터 캐싱, 백그라운드 작업 큐 |
| Task Queue | Celery + Redis | 주기적 데이터 수집, 비동기 리포트 생성 |
| AI | Claude API (Anthropic) | 한국어 분석 품질 우수, 긴 컨텍스트 지원 |
| 한국 데이터 | DART OpenAPI + KRX API + PyKRX | 공시 + 시세 + 뉴스 |
| 미국 데이터 | yfinance + NewsAPI | 시세 + 영문 뉴스. yfinance는 무료, NewsAPI 무료 플랜 100건/일 |
| Push | pywebpush + Service Worker | Web Push API 표준. VAPID 키 기반 인증 |
| ORM | SQLAlchemy 2.0 | FastAPI와 호환, 타입 지원 |
| Auth | JWT (PyJWT) + bcrypt | 간단하고 검증된 인증 |

## Key Decisions

### 모놀리식 단일 저장소
**선택**: 백엔드 + 프론트엔드를 하나의 저장소에서 관리
**대안**: 마이크로서비스, 별도 저장소
**이유**: MVP 단계에서 단순성 유지. 에이전트가 전체 코드를 파악하기 용이
**트레이드오프**: 스케일링 유연성 제한
**재검토 시점**: 일일 사용자 10,000명 이상 시

### Celery 백그라운드 워커
**선택**: Celery + Redis로 주가 수집/분석을 비동기 처리
**대안**: APScheduler (인프로세스), AWS Lambda
**이유**: 주기적 작업(30분 간격 수집) + 비동기 작업(리포트 생성) 모두 처리. 검증된 조합
**트레이드오프**: Redis 인프라 추가 필요
**재검토 시점**: 서버리스 마이그레이션 검토 시

### Claude API for 분석
**선택**: Anthropic Claude API
**대안**: OpenAI GPT-4o, 로컬 LLM
**이유**: 한국어 분석 품질 우수, 긴 컨텍스트 윈도우 (뉴스 다수 포함 가능)
**트레이드오프**: API 비용, 외부 의존
**재검토 시점**: 비용이 월 $2,000 초과 시 또는 로컬 LLM 품질이 충분해질 때

### PostgreSQL + JSONB
**선택**: 분석 결과를 JSONB로 저장
**대안**: 별도 NoSQL, 정규화된 테이블
**이유**: 리포트 분석 결과의 구조가 유동적 (원인 수, 출처 수 가변). JSONB로 유연하게 저장하되 PostgreSQL의 쿼리 기능 유지
**트레이드오프**: JSONB 내부 쿼리 성능 제한
**재검토 시점**: 리포트 검색 기능 고도화 시

### 한국/미국 종목 통합 모델
**선택**: 동일 stocks 테이블에 market 컬럼(KRX/NYSE/NASDAQ)으로 구분
**대안**: 시장별 별도 테이블
**이유**: 관심목록, 리포트, 수집기 등 하위 로직이 시장과 무관하게 stock_id만 참조하면 되므로 단일 테이블이 간결
**트레이드오프**: 한국 종목(name_kr 등)과 미국 종목의 필드 차이를 nullable로 처리

### 유사 케이스 매칭 — DB 기반 검색
**선택**: PriceSnapshot 테이블에서 직접 SQL 쿼리로 유사 변동률 검색
**대안**: 벡터 DB, 전용 시계열 DB
**이유**: MVP 단계에서 데이터량이 적어 SQL로 충분. 추가 인프라 불필요
**재검토 시점**: 종목 수 1,000+ & 일일 스냅샷 10,000+ 시 성능 저하 가능

### Redis 캐싱 전략 (project-003)
**선택**: 시세 데이터와 트렌딩/인기 종목을 Redis에 캐싱 (TTL 5분)
**이유**: 시세 조회가 가장 빈번한 API인데, 매번 DB 조회 + 서브쿼리는 비효율적. graceful degradation — Redis 다운 시 DB 직접 조회
**트레이드오프**: 최대 5분 지연 데이터 제공 가능

### 시세 신선도(Freshness) 모델 (project-003)
**선택**: price_freshness 필드로 live/delayed/stale/unavailable 4단계 구분
**이유**: 장중/장외, 수집 주기에 따라 시세 데이터의 신뢰도가 다름. 사용자에게 데이터 품질을 명시적으로 전달

### 커뮤니티 — 1단계 댓글 (project-003)
**선택**: 대댓글 없이 토론→댓글 1단계만 지원
**대안**: 대댓글 트리, 스레드형
**이유**: MVP에서 복잡한 트리 구조는 과도. 토론당 최대 100개 댓글 제한으로 단순성 유지
**재검토 시점**: 커뮤니티 활성화 후 사용자 피드백 기반
