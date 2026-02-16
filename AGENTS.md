# oh-my-stock

주가 급변동 시 AI가 원인을 심층 분석해주는 독립 웹 서비스.

## Docs

- **PRD & 기능 명세** → `docs/prd.md`
- **아키텍처 & 데이터 모델** → `docs/architecture.md`
- **코딩 컨벤션 & 테스트** → `docs/conventions.md`
- **기술 스택 & 셋업** → `docs/tech_stack.md`

## Absolute Rules

1. **테스트를 수정하지 마라.** 테스트가 실패하면 구현 코드를 고쳐라.
2. **커밋 전 반드시** `.forge/scripts/test_fast.sh` 실행.
3. **기능 완료 시** `.forge/projects/current/features.json`의 status를 "done"으로 업데이트.
4. **새 기능 발견 시** `docs/backlog.md`에 추가. features.json의 scope를 절대 변경하지 마라.
5. **파일 300줄 초과 금지.** 초과 시 분리.
6. **외부 API 호출은 반드시 mock 테스트.** DART, KRX, Claude API 직접 호출 테스트 금지.
7. **타입 힌트 필수** (Python), **strict mode 필수** (TypeScript).

## Session Start

```bash
source .forge/scripts/init.sh
```

## Project Context

- 현재 프로젝트: `.forge/projects/current/`
- 기능 보드: `.forge/projects/current/features.json`
- 진행 로그: `.forge/projects/current/progress.txt`
- 가장 높은 우선순위의 pending 기능부터 작업하라.
