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
