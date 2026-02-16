# Architecture: oh-my-stock

## System Type

모놀리식 아키텍처 (MVP). 백엔드(Python/FastAPI)와 프론트엔드(Next.js)를 분리하되, 단일 저장소에서 관리.

```
[Browser] → [Next.js Frontend] → [FastAPI Backend] → [PostgreSQL]
                                        ↓
                                  [Background Workers]
                                   ├── 주가 수집기
                                   ├── 뉴스/공시 수집기
                                   └── AI 분석 엔진
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
| ORM | SQLAlchemy 2.0 | FastAPI와 호환, 타입 지원 |
| Auth | JWT (PyJWT) + bcrypt | 간단하고 검증된 인증 |

## Directory Structure

```
oh-my-stock/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI 앱 엔트리포인트
│   │   ├── config.py              # 환경 설정
│   │   ├── models/                # SQLAlchemy 모델
│   │   │   ├── user.py
│   │   │   ├── stock.py
│   │   │   ├── watchlist.py
│   │   │   └── report.py
│   │   ├── api/                   # API 라우터
│   │   │   ├── auth.py
│   │   │   ├── stocks.py
│   │   │   ├── watchlist.py
│   │   │   └── reports.py
│   │   ├── services/              # 비즈니스 로직
│   │   │   ├── stock_service.py
│   │   │   ├── analysis_service.py
│   │   │   └── report_service.py
│   │   ├── workers/               # Celery 태스크
│   │   │   ├── price_collector.py
│   │   │   ├── news_collector.py
│   │   │   └── analyzer.py
│   │   ├── clients/               # 외부 API 클라이언트
│   │   │   ├── dart_client.py
│   │   │   ├── krx_client.py
│   │   │   └── llm_client.py
│   │   └── db/
│   │       ├── database.py
│   │       └── migrations/
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/                   # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx           # 랜딩/대시보드
│   │   │   ├── login/
│   │   │   ├── signup/
│   │   │   ├── dashboard/
│   │   │   └── reports/[id]/
│   │   ├── components/            # React 컴포넌트
│   │   │   ├── StockCard.tsx
│   │   │   ├── ReportView.tsx
│   │   │   ├── WatchlistManager.tsx
│   │   │   └── AlertBadge.tsx
│   │   ├── lib/                   # 유틸리티
│   │   │   ├── api.ts             # API 클라이언트
│   │   │   └── auth.ts            # 인증 헬퍼
│   │   └── types/                 # TypeScript 타입
│   ├── package.json
│   └── tsconfig.json
├── tests/
│   ├── backend/
│   │   ├── test_api_auth.py
│   │   ├── test_api_stocks.py
│   │   ├── test_api_watchlist.py
│   │   ├── test_api_reports.py
│   │   ├── test_service_analysis.py
│   │   └── test_worker_collector.py
│   └── frontend/
│       └── ...
├── docs/
├── AGENTS.md
└── docker-compose.yml
```

## Data Model

### users
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | bcrypt |
| created_at | TIMESTAMP | |
| settings | JSONB | 변동률 임계값 등 |

### stocks
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| code | VARCHAR(20) | 종목코드 (예: 005930) |
| name | VARCHAR(100) | 종목명 (예: 삼성전자) |
| market | VARCHAR(10) | KRX / NYSE / NASDAQ |
| sector | VARCHAR(100) | 업종 |

### watchlists
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK → users |
| stock_id | UUID | FK → stocks |
| threshold | FLOAT | 변동률 임계값 (기본 3.0) |
| created_at | TIMESTAMP | |

### price_snapshots
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| stock_id | UUID | FK → stocks |
| price | DECIMAL | 현재가 |
| change_pct | FLOAT | 전일 대비 변동률 |
| volume | BIGINT | 거래량 |
| captured_at | TIMESTAMP | 수집 시점 |

### reports
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| stock_id | UUID | FK → stocks |
| trigger_price | DECIMAL | 변동 감지 시점 가격 |
| trigger_change_pct | FLOAT | 변동률 |
| summary | TEXT | 1줄 요약 |
| analysis | JSONB | 상세 분석 (원인들, 확신도, 출처) |
| status | VARCHAR(20) | pending / generating / completed / failed |
| created_at | TIMESTAMP | |
| completed_at | TIMESTAMP | |

### report_sources
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| report_id | UUID | FK → reports |
| source_type | VARCHAR(20) | news / disclosure / market_data |
| title | VARCHAR(500) | |
| url | VARCHAR(1000) | |
| published_at | TIMESTAMP | |

## API Design

### 인증
- `POST /api/auth/signup` — 회원가입
- `POST /api/auth/login` — 로그인 (JWT 반환)
- `POST /api/auth/refresh` — 토큰 갱신

### 종목
- `GET /api/stocks/search?q={query}` — 종목 검색

### 관심 목록
- `GET /api/watchlist` — 내 관심 목록 (현재가 포함)
- `POST /api/watchlist` — 종목 추가
- `DELETE /api/watchlist/{id}` — 종목 제거
- `PATCH /api/watchlist/{id}` — 임계값 수정

### 리포트
- `GET /api/reports` — 내 관심 종목 리포트 목록 (최신순)
- `GET /api/reports/{id}` — 리포트 상세
- `GET /api/reports/stock/{stock_id}` — 특정 종목 리포트 목록

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
