# Project 004: deep-analysis-pipeline

## Goal
분석 깊이 강화 + 실데이터 파이프라인 구축 + 기반 정비. 단순 뉴스 요약 수준을 넘어 사용자가 직접 할 수 없는 깊이 있는 AI 분석을 제공하고, 실제 시장 데이터를 수집·연동하는 파이프라인을 완성한다.

## Context
- project-001~003에서 F1~F18 전 기능을 넓게 구현 완료
- 회고 핵심 교훈: "넓이보다 깊이. 분석 차별화에 집중."
- 현재 AI 분석: 뉴스 나열 + 1줄 요약 수준. 차별화 포인트 부족
- 현재 데이터: mock 위주, 실데이터 파이프라인 미검증
- 레거시 버그: 대시보드 헤더 중복, Alembic 마이그레이션 미설정

## Scope
1. **분석 깊이 강화** (핵심)
   - 섹터 연쇄 영향 분석
   - 유사 케이스 이후 주가 추이 비교
   - 다층 원인 분석 (직접→간접→시장환경)
   - 단기/중기 전망 섹션
   - 뉴스 감성 분석 트렌드

2. **실데이터 파이프라인**
   - KRX/yfinance 실시세 수집 안정화
   - DART 공시 + 뉴스 실연동
   - Celery Beat 스케줄링 실동작
   - 수집 모니터링

3. **기반 정비**
   - 헤더 중복 버그 수정
   - Alembic 마이그레이션
   - 시드 데이터 인프라
   - DB 커넥션 풀 안정화

## Out of Scope
- 새로운 UI 페이지/기능 추가
- 실시간 WebSocket 시세 스트리밍
- 모바일 네이티브 앱

## Definition of Done
- All features in features.json are "done"
- All tests pass (including all previous tests)
- No regressions
- 실데이터 수집이 최소 1시간 이상 안정적으로 동작
- AI 분석 리포트가 기존 대비 깊어진 결과물 생성
