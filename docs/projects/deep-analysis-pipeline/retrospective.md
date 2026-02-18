# Retrospective: deep-analysis-pipeline

## Summary
2026-02-18 → 2026-02-18 | 4 sessions | 16 features completed

## Goal
분석 깊이 강화 + 실데이터 파이프라인 구축 + 기반 정비. AI 분석 차별화와 실제 데이터 연동을 통해 프로토타입에서 실서비스 수준으로 도약.

## What Was Built
- **기반 정비 (4건)**: 레거시 헤더 제거, Alembic 마이그레이션 초기 설정, 시드 데이터 스크립트, DB 커넥션 풀 안정화
- **데이터 파이프라인 (6건)**: KRX 실시세 수집(PyKRX), 미국 시세 수집(yfinance), DART 공시 수집, 뉴스 수집(NAVER+NewsAPI), 파이프라인 모니터링 API, 급변동 감지→리포트 생성 E2E 파이프라인
- **분석 고도화 (6건)**: 다층 원인 분석(직접/간접/거시), 단기/중기 전망 섹션, 섹터 연쇄 영향 분석, 유사 케이스 이후 주가 추이, 뉴스 감성 트렌드(SVG 차트), 리포트 UI 고도화(탭/뱃지/fallback)

## What Wasn't Built (and Why)
- 계획된 16개 기능 전부 완료. 지연된 항목 없음.

## What Went Well
- **16/16 완료**: 하루 4세션 만에 전체 기능 구현 완료. 기반 정비 → 파이프라인 → 분석 순서로 의존성을 존중하며 진행
- **테스트 커버리지**: 1,752 tests passed. 모든 기능에 테스트 포함
- **E2E 파이프라인 설계**: 가격수집→급변동감지→뉴스수집→AI분석→알림의 5단계 Celery chain이 에러 격리와 함께 깔끔하게 구성됨
- **graceful fallback**: 구 형식 리포트와 신 형식 리포트가 공존 가능하도록 설계 (다층 분석 없으면 flat causes 렌더링)

## What Could Be Improved
- **SentimentTrend import 버그**: 새 컴포넌트(`SentimentTrend.tsx`)에서 `{ api }` (named import)로 가져왔으나 실제로는 default export. 종목 상세 페이지 크래시 유발. 새 파일 작성 시 기존 모듈의 export 방식을 반드시 확인해야 함
- **시드 데이터와 새 스키마 불일치**: 시드 데이터는 구 형식(`causes[{title, description}]`)을 사용하는데, 프론트엔드는 새 형식(`reason`, `impact`)을 기대. 리포트 상세에서 원인 텍스트가 빈칸으로 표시됨
- **Alembic과 create_tables 이중 관리**: DB 스키마 관리가 Alembic과 SQLAlchemy create_tables() 두 곳에서 이루어져 충돌 가능. stamp 후 수동 ALTER TABLE이 필요했음
- **미구현 기능 발견 (e2e 테스트에서)**: 알림 페이지(404), 로그아웃 UI 미노출, AI 판단 로직 미정의, 종목 리스트 동적 반영 미구현

## Harness Improvements
- 특별한 하네스 변경 없음. 기존 forge 하네스가 안정적으로 동작

## Lessons for Next Project
- **새 파일 작성 시 import 검증 필수**: 기존 모듈의 default/named export 방식을 확인하는 규칙을 AGENTS.md에 추가해야 함
- **시드 데이터를 새 스키마와 동기화**: 분석 JSONB 구조를 변경할 때 시드 데이터도 함께 업데이트해야 실서비스 테스트가 의미 있음
- **DB 마이그레이션 단일 경로**: Alembic을 도입했으면 create_tables()는 제거하고 Alembic만 사용하는 것이 안전
- **e2e 스모크 테스트를 코딩 세션 중에 실행**: 기능 구현 후 실제 서비스를 띄워보는 것이 유닛 테스트만으로는 놓치는 버그를 잡아냄
