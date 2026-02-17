# Project 002: p1-ux-expansion

## Goal
P0 품질 보강 + P1 전체 기능 구현. 매 세션이 끝날 때마다 실제 사용자가 체감할 수 있는 완성도를 확보한다.

## Context
mvp-core-features에서 P0 16개 기능을 완료했으나, 회고에서 실제 서비스 동작 미검증/UX 미흡/보안 경고 등의 품질 이슈가 확인됨. 이번 프로젝트는 4단계로 나뉘며, 각 단계 완료 시 실제 서비스를 기동하여 사용자 시나리오를 검증한다.

## Scope
- **Phase 1 — 기존 앱 완성도 확보** (세션 1): CORS/시드 통합 수정, JWT 보안, 검색 UX 전면 개선, 임계값 UI, 전역 에러/로딩 UX → 한국 주식 사용자가 불편 없이 사용 가능한 상태
- **Phase 2 — 알림 시스템** (세션 2): 푸시 구독, 발송 워커, 알림 UI, 알림 히스토리 → 급변동 시 즉시 알림을 받는 경험 완성
- **Phase 3 — 미국 주식** (세션 3): 시드, 검색, 수집기, 뉴스 수집, 분석, 통합 UI → 미국 주식도 한국과 동일한 수준으로 사용 가능
- **Phase 4 — 유사 케이스 매칭** (세션 4): 매칭 엔진, 추이 데이터, 리포트 통합, UI → 리포트에서 과거 유사 사례 비교 분석까지 제공

## Out of Scope
- P2 기능 (장기 트렌드, 리포트 공유, 커뮤니티 토론)
- 모바일 네이티브 앱
- 실시간 WebSocket 주가 스트리밍
- 소셜 로그인

## Definition of Done
- All features in features.json are "done"
- All tests pass (including all previous tests)
- No regressions
- 각 Phase 마지막 통합 검증 기능에서 실제 서비스 기동 확인
