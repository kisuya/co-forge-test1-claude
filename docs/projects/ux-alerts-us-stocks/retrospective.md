# Retrospective: ux-alerts-us-stocks

## Summary
2026-02-17 → 2026-02-17 | 1 session | 24 features completed

## Goal
P0 품질 보강 + P1 전체 기능 구현. 매 세션 완료 시 실제 사용자가 체감할 수 있는 완성도 확보.

## What Was Built
- **Phase 1 — 한국 주식 사용 완성도 (8개)**
  - infra-002: CORS 미들웨어 + 시드 데이터 자동 실행 (이전 retro 지적 반영)
  - auth-004: JWT 시크릿 키 32바이트 강제, 만료 시 명확한 에러 코드 반환
  - ui-004: 종목 검색 디바운스(300ms) + 자동검색 + AbortController
  - ui-005: 검색 결과 하이라이트, 종목 추가 후 자동 닫힘, 이미 추가된 종목 뱃지
  - ui-006: 최근 검색어 localStorage 저장 (최대 10개, FIFO)
  - ui-007: 임계값 설정 인라인 패널 (±0.5% 스텝퍼, 1%~10%)
  - ui-010: 전역 에러 바운더리, 토스트, empty state 처리
  - infra-003: Phase 1 통합 검증 (한국 주식 시나리오 e2e)

- **Phase 2 — 알림 시스템 (4개)**
  - alert-001: PushSubscription 모델 + subscribe/unsubscribe/status API
  - alert-002: Celery 푸시 발송 워커 (재시도 3회, 만료 구독 자동 비활성화)
  - alert-003: 알림 설정 UI (사이드 패널, 전체/종목별 토글, Service Worker)
  - alert-004: Phase 2 통합 검증

- **Phase 3 — 미국 주식 (7개)**
  - stock-002: S&P 500 시드 데이터 (100+ 종목, market 컬럼 구분)
  - stock-003: 미국 주식 검색 + 한글 별명 지원 ("애플" → AAPL)
  - data-004: yfinance 기반 미국 주가 수집기 (30분 간격, 서머타임 고려)
  - data-005: 영문 뉴스 수집기 (1시간 캐싱, 일일 호출 제한 고려)
  - analysis-003: 미국 주식 한국어 분석 리포트 (프리마켓/FOMC/환율 컨텍스트)
  - ui-008: 시장 탭(전체/한국/미국), 시장 뱃지(KRX/NYSE/NASDAQ)
  - stock-004: Phase 3 통합 검증

- **Phase 4 — 유사 케이스 (5개)**
  - case-001: 유사 과거 변동 매칭 엔진 (±1.5%p, 상위 3건)
  - case-002: 이후 주가 추이 API (1주/1개월 누적 변동률)
  - case-003: 리포트 생성 파이프라인에 유사 사례 통합
  - ui-009: 유사 케이스 UI (접이식 섹션, 유사도 뱃지, 모바일 스택)
  - case-004: Phase 4 통합 검증

## What Wasn't Built (and Why)
모든 24개 기능이 구현됨. 보류된 기능 없음.

## What Went Well
- 24개 기능을 1세션에 전부 완료 — Phase 4까지 의존성 순서를 지키며 체계적으로 구현
- 409개 테스트 전부 통과 (2개 skip), 0개 실패
- 이전 retro 지적사항이 정확히 반영됨: CORS 자동 설정, 시드 데이터 자동 실행, JWT 키 길이 강제, 검색 UX 전면 개선
- 실제 서비스 기동 확인 — 회원가입 → 로그인 → 검색 → 관심목록 → 임계값 → 알림까지 전체 사용자 플로우 동작
- 한국/미국 종목이 대시보드에서 자연스럽게 혼합 표시되는 통합 UX

## What Could Be Improved
- **실시간 시세 미연동**: StockCard에 가격이 "-"로 표시됨. 수집기는 있지만 대시보드에 실시간 반영하는 연결이 없음
- **에러 응답 일관성**: Cases API가 존재하지 않는 report_id에 404 대신 500 반환. 방어적 에러 처리 부족
- **CORS + 500 에러 조합**: 서버 500 응답에 CORS 헤더가 누락되어 브라우저에서 CORS 에러로 오인 — 디버깅 혼란 유발

## Harness Improvements
- AGENTS.md에 "API 엔드포인트는 존재하지 않는 리소스에 대해 반드시 404를 반환할 것 (500 금지)" 규칙 추가 권장
- 에러 응답에서도 CORS 헤더가 포함되는지 검증하는 테스트 추가 권장

## Lessons for Next Project
- 수집기(worker)와 UI를 연결하는 "실시간 데이터 표시" 기능을 별도로 스코핑할 것 — 수집만 하고 표시 안 하면 사용자가 체감 못 함
- 방어적 에러 처리(404 vs 500)를 features.json 수용 기준에 명시할 것
- 미들웨어(CORS 등)가 에러 응답에서도 정상 동작하는지 통합 테스트에 포함할 것
