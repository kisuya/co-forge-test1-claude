# Project 1: MVP 기반 구축

## Goal
oh-my-stock의 핵심 기능(P0) 전체를 구현한다. 사용자 인증, 종목 검색/관심목록, 주가 급변동 감지, AI 분석 리포트, 대시보드까지 엔드투엔드로 작동하는 MVP를 완성한다.

## Context
첫 번째 프로젝트. 기존 코드 없음. 아키텍처(docs/architecture.md)에 정의된 기술 스택(FastAPI + Next.js + PostgreSQL + Redis + Celery)을 기반으로 프로젝트 골격부터 구축한다.

## Scope
- 프로젝트 인프라 셋업 (백엔드/프론트엔드 스켈레톤, DB, Docker)
- 사용자 인증 (회원가입, 로그인, JWT) — PRD F5
- 한국 주식 종목 검색 및 관심목록 CRUD — PRD F1
- 주가 수집 + 급변동 감지 (Celery 워커) — PRD F2
- 뉴스/공시 수집 + AI 분석 리포트 생성 — PRD F3
- 웹 대시보드 (관심목록, 리포트 조회, 반응형) — PRD F4

## Out of Scope
- 미국 주식 지원 (P1 — F6)
- 유사 과거 케이스 매칭 (P1 — F7)
- 웹 푸시 알림 (P1 — F8)
- 장기 트렌드 분석, 리포트 공유, 커뮤니티 (P2 — F9~F11)
- 소셜 로그인
- 모바일 네이티브 앱

## Definition of Done
- All features in features.json are "done"
- All tests pass (including all previous tests)
- No regressions
