# oh-my-stock

주가 급변동 시 AI가 원인을 심층 분석해주는 독립 웹 서비스.

## Product Requirements
→ docs/prd.md

## Architecture
→ docs/architecture.md

## Coding Conventions
→ docs/conventions.md

## Tech Stack
→ docs/tech_stack.md

## Absolute Rules

1. **테스트를 수정하지 마라.** 테스트가 실패하면 구현 코드를 고쳐라.
2. **모든 새 기능에는 테스트를 포함하라.**
3. **기능 완료 전 반드시** `.forge/scripts/test_fast.sh` 실행.
4. **git commit을 직접 실행하지 마라.** checkpoint.sh가 세션 간 커밋을 처리한다.
5. **기능 완료 시** `docs/projects/current/features.json`의 status를 "done"으로 업데이트.
6. **새 기능 발견 시** `docs/backlog.md`에 추가. features.json의 scope를 절대 변경하지 마라.
7. **하나의 파일, 하나의 책임.** 여러 관심사가 섞이면 분리.
8. **외부 API 호출은 반드시 mock 테스트.** DART, KRX, Claude API 직접 호출 테스트 금지.
9. **통합 검증 필수.** 프론트엔드 구현 시 CORS/시드 등 통합 조건 확인. 모든 기능 완료 후 실제 서비스 기동하여 e2e 스모크 테스트 1회 수행.
10. **API 에러 응답은 적절한 HTTP 상태 코드를 반환하라.** 존재하지 않는 리소스는 404, 유효하지 않은 입력은 422. 500은 예상치 못한 서버 오류에만 사용.
11. **새 글로벌 컴포넌트가 기존 컴포넌트를 대체하면, 기존 것을 반드시 삭제하라.** 추가만 하고 제거를 잊으면 중복 렌더링 버그가 발생한다. (예: 글로벌 헤더 추가 시 페이지별 레거시 헤더 제거)
12. **넓이보다 깊이를 우선하라.** 기능 수를 채우는 것보다 각 기능의 차별화 수준이 중요하다. 특히 AI 분석은 서비스의 핵심 가치이므로, 단순 요약이 아닌 깊이 있는 분석(유사 케이스 비교, 섹터 연쇄 영향, 시계열 패턴)을 구현하라.
13. **새 파일에서 기존 모듈을 import할 때 export 방식을 반드시 확인하라.** `export default`이면 `import X from`, `export const`이면 `import { X } from`. 잘못된 import는 런타임 크래시를 유발한다.
14. **시드 데이터는 현재 스키마와 동기화하라.** 모델이나 JSONB 구조를 변경하면 `seed_sample_data.py`도 함께 업데이트. 실서비스 테스트에서 빈칸/크래시 방지.

## Session Start Protocol

1. `source .forge/scripts/init.sh` 실행
2. 출력을 읽고 현재 프로젝트 상태 파악
3. `features.json`에서 가장 높은 우선순위의 pending 기능 선택
4. 구현 → 테스트 작성 → 테스트 통과 확인
5. `features.json` status를 "done"으로 업데이트
6. 다음 기능으로 이동 (커밋하지 마라 — checkpoint.sh가 처리)

## Project Context

- 현재 스펙: `docs/projects/current/spec.md`
- 기능 보드: `docs/projects/current/features.json`
- 진행 로그: `docs/projects/current/progress.txt`
- 이전 프로젝트: `docs/projects/` (읽기 전용 참고)
- 백로그: `docs/backlog.md` (코딩 중 append-only)
