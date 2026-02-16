# Conventions: oh-my-stock

## Language & Style

### Backend (Python)
- Python 3.12+
- 타입 힌트 필수 (모든 함수 파라미터 + 리턴 타입)
- formatter: ruff format
- linter: ruff check
- 독스트링: 공개 함수만, Google style

### Frontend (TypeScript)
- TypeScript strict mode
- formatter: prettier
- linter: eslint
- React: 함수형 컴포넌트 + hooks only

## Naming

### Backend
- 파일명: snake_case (`stock_service.py`)
- 클래스: PascalCase (`StockService`)
- 함수/변수: snake_case (`get_stock_price`)
- 상수: UPPER_SNAKE_CASE (`MAX_WATCHLIST_SIZE`)
- API 경로: kebab-case 아닌 snake 없이 소문자 (`/api/watchlist`)

### Frontend
- 파일명: PascalCase 컴포넌트 (`StockCard.tsx`), camelCase 유틸리티 (`api.ts`)
- 컴포넌트: PascalCase (`StockCard`)
- 함수/변수: camelCase (`fetchReports`)
- 타입/인터페이스: PascalCase (`Report`, `StockData`)

## File Organization

- 파일 최대 300줄. 초과 시 분리
- 하나의 파일에 하나의 주요 책임
- import 순서: 표준 라이브러리 → 서드파티 → 로컬

## Error Handling

### Backend
- API 에러: HTTPException with 적절한 status code
- 외부 API 에러: 재시도 1회 후 로깅, 사용자에게 graceful 메시지
- 비즈니스 로직 에러: 커스텀 예외 클래스 사용 (`app/exceptions.py`)

### Frontend
- API 호출 실패: toast 알림으로 사용자 안내
- 로딩 상태: skeleton UI 표시

## Testing

### Backend
- 프레임워크: pytest
- 테스트 파일: `tests/backend/test_{module}.py`
- 테스트 함수: `test_{기능}_{시나리오}_{기대결과}` (예: `test_login_invalid_password_returns_401`)
- 커버리지 목표: 핵심 서비스 80%+
- 외부 API: 반드시 mock 처리

### Frontend
- 프레임워크: vitest + React Testing Library
- 테스트 파일: `{Component}.test.tsx`

## Git Commit Format

```
<type>: <short description>

<optional body>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

예시:
- `feat: add watchlist API endpoints`
- `fix: handle DART API timeout gracefully`
- `test: add analysis service unit tests`
