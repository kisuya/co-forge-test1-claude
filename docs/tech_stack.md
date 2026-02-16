# Tech Stack: oh-my-stock

## Quick Reference

| 항목 | 선택 | 버전 |
|------|------|------|
| **Runtime** | Python | 3.12+ |
| **Backend Framework** | FastAPI | 0.115+ |
| **Frontend Runtime** | Node.js | 20 LTS |
| **Frontend Framework** | Next.js (App Router) | 15 |
| **Language (FE)** | TypeScript | 5.x |
| **Database** | PostgreSQL | 16 |
| **Cache / Queue Broker** | Redis | 7 |
| **Task Queue** | Celery | 5.4+ |
| **ORM** | SQLAlchemy | 2.0+ |
| **Migration** | Alembic | 1.13+ |
| **Auth** | PyJWT + bcrypt | |
| **AI** | Anthropic Claude API | claude-sonnet-4-5 |
| **KR 시세** | PyKRX + KRX Open API | |
| **KR 공시** | DART OpenAPI | |
| **Testing (BE)** | pytest + pytest-asyncio | |
| **Testing (FE)** | vitest + React Testing Library | |
| **Linter (BE)** | ruff | |
| **Formatter (BE)** | ruff format | |
| **Linter (FE)** | eslint | |
| **Formatter (FE)** | prettier | |
| **Container** | Docker + docker-compose | |

## Key Dependencies (Backend)

```
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
asyncpg
alembic
celery[redis]
redis
pyjwt
bcrypt
httpx
anthropic
pykrx
python-dotenv
ruff
pytest
pytest-asyncio
```

## Key Dependencies (Frontend)

```
next
react
react-dom
typescript
tailwindcss
@tanstack/react-query
axios
zustand
vitest
@testing-library/react
```

## Setup Commands

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Frontend
cd frontend
npm install
npm run dev

# Infrastructure (Docker)
docker-compose up -d postgres redis

# Run tests
cd backend && pytest
cd frontend && npm test
```

## Environment Variables

```env
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ohmystock
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-...
DART_API_KEY=...
JWT_SECRET_KEY=...
JWT_EXPIRY_HOURS=168

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```
