# Retrospective: mvp-core-features

## Summary
2026-02-16 → 2026-02-16 | 3 sessions | 16 features completed

## Goal
oh-my-stock MVP 전체 P0 기능 구현 (인증, 종목관리, 급변동감지, AI리포트, 대시보드)

## What Was Built
- infra-001: 백엔드 프로젝트 스켈레톤 (FastAPI, config, docker-compose)
- db-001: 데이터베이스 모델 및 마이그레이션 (User, Stock, Watchlist, PriceSnapshot, Report, ReportSource)
- auth-001/002/003: 회원가입, 로그인/JWT, 인증 미들웨어
- stock-001: 한국 주식 데이터 시드 및 검색 API
- watch-001: 관심목록 CRUD API
- data-001/002/003: 주가 수집 워커, 급변동 감지, 뉴스/공시 수집기
- analysis-001/002: LLM 분석 엔진, 리포트 생성 파이프라인
- report-001: 리포트 API 엔드포인트
- ui-001/002/003: 프론트엔드 스켈레톤, 대시보드/관심목록 UI, 리포트 조회/반응형

## What Wasn't Built (and Why)
모든 P0 기능이 구현됨. 보류된 기능 없음.

## What Went Well
- 하루 만에 16개 기능 전체 완료 — 빠른 실행력
- 96개 테스트 전부 통과, 0개 실패
- 커밋 컨벤션이 일관됨 ([feature-id] 접두사)
- 의존성 순서를 지켜 체계적으로 구현 (infra → db → auth → stock → data → analysis → ui)

## What Could Be Improved
- **테스트만 통과시키고 실제 동작은 검증 안 함**: seed_stocks()를 함수만 만들고 앱 시작 시 실행하지 않아 DB가 빈 상태로 서비스 기동됨. CORS 미들웨어 누락으로 프론트→백엔드 통신 불가. 테스트는 통과했지만 실제 서비스는 작동하지 않는 상태.
- **UX 미흡**: 종목 추가 후 검색 결과가 닫히지 않음. 검색 UX 전반적으로 개선 필요 (디바운스, 자동검색, 빈 결과 안내 등).
- **JWT 시크릿 키 길이 경고**: 테스트 환경에서 32바이트 미만 키 사용 (InsecureKeyLengthWarning 25건).

## Harness Improvements
- 에이전트가 기능 완료 후 `실제 서비스 기동 + e2e 스모크 테스트`를 수행하도록 AGENTS.md에 규칙 추가 필요
- 프론트엔드 ↔ 백엔드 통합 검증 단계를 체크포인트에 포함시켜야 함

## Lessons for Next Project
- 단위 테스트 통과 ≠ 서비스 동작. 다음부터는 최소 1회 실제 기동 검증을 의무화할 것
- seed/migration 같은 초기화 로직은 앱 시작이나 CLI 커맨드로 반드시 연결할 것
- CORS 같은 인프라 설정은 프론트엔드 기능 구현 시 체크리스트에 포함할 것
- UX 관련 수용 기준을 features.json에 명시적으로 기술할 것
