# oh-my-stock

주가 급변동 시 AI가 원인을 심층 분석해주는 독립 웹 서비스.

## Architecture
→ docs/architecture.md

## Coding Conventions
→ docs/conventions.md

## Tech Stack
→ docs/tech_stack.md

## Absolute Rules

1. **테스트를 수정하지 마라.** 테스트가 실패하면 구현 코드를 고쳐라.
2. **모든 새 기능에는 테스트를 포함하라.**
3. **커밋 전 반드시** `.forge/scripts/test_fast.sh` 실행.
4. **기능 완료 시** `docs/projects/current/features.json`의 status를 "done"으로 업데이트.
5. **새 기능 발견 시** `docs/backlog.md`에 추가. features.json의 scope를 절대 변경하지 마라.
6. **파일 300줄 초과 금지.** 초과 시 분리.
7. **외부 API 호출은 반드시 mock 테스트.** DART, KRX, Claude API 직접 호출 테스트 금지.
8. **통합 검증 필수.** 프론트엔드 구현 시 CORS/시드 등 통합 조건 확인. 모든 기능 완료 후 실제 서비스 기동하여 e2e 스모크 테스트 1회 수행.

## Session Start Protocol

1. `source .forge/scripts/init.sh` 실행
2. 출력을 읽고 현재 프로젝트 상태 파악
3. `features.json`에서 가장 높은 우선순위의 pending 기능 선택
4. 구현 → 테스트 작성 → 테스트 통과 확인
5. 커밋 (`[feature-id] 설명` 형식)
6. `features.json` status를 "done"으로 업데이트
7. 다음 기능으로 이동

## Project Context

- 현재 스펙: `docs/projects/current/spec.md`
- 기능 보드: `docs/projects/current/features.json`
- 진행 로그: `docs/projects/current/progress.txt`
- 이전 프로젝트: `docs/projects/` (읽기 전용 참고)
- 백로그: `docs/backlog.md` (코딩 중 append-only)
