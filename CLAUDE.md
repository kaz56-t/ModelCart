# ModelCart — Agent Commerce API

LLM/AIエージェント特化型の通販API。APIキーとポリシー設定だけでAIエージェントが自律的に商品検索・注文できる。

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (Python 3.12) |
| DB | PostgreSQL (JSONB for policies/order items) |
| ORM | SQLAlchemy async + asyncpg |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | Bearer Token (API keys, SHA256 hashed) |
| Admin UI | Next.js |
| Container | Docker + docker-compose |
| Deploy | Railway |

## Project Structure

```
agent-commerce/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app, router registration, CORS
│   │   ├── database.py           # SQLAlchemy async engine
│   │   ├── models/               # product, order, api_key, delivery_profile, order_log
│   │   ├── routers/              # search.py, products.py, orders.py
│   │   ├── services/             # policy_engine.py, auth.py, inventory.py
│   │   └── schemas/              # Pydantic schemas
│   ├── migrations/               # Alembic
│   ├── Dockerfile
│   ├── railway.toml
│   ├── pyproject.toml
│   └── .env.example
├── admin-ui/                     # Next.js admin panel
│   └── package.json
├── docker-compose.yml
└── docs/
    └── agent-commerce-spec.md    # Full specification (Japanese)
```

## Common Commands

### Backend

```bash
# Start local dev environment
docker-compose up

# Run backend only
uvicorn app.main:app --reload

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"

# Tests
pytest
pytest --cov=app

# Lint / format
ruff check . --fix
black .
mypy app/
```

### Admin UI

```bash
cd admin-ui
npm install
npm run dev
npm run build
npm run lint
```

## Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
SECRET_KEY=your-secret-key-here
API_KEY_PREFIX=sk-agent-
ALLOWED_ORIGINS=https://your-admin-ui.vercel.app
```

## API Endpoints

All endpoints (except `/health`) require `Authorization: Bearer sk-agent-xxxxxxxx`.

Every response includes an `agent_hint` field to guide LLM next actions.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (no auth) |
| POST | `/v1/search` | Product search with filters |
| GET | `/v1/products/{id}` | Product detail |
| POST | `/v1/orders` | Create order (supports `dry_run: true`) |
| GET | `/v1/orders/{id}` | Order status |

## Policy Engine

Each API key has a `policy` JSONB field controlling agent behavior:

| Field | Type | Description |
|-------|------|-------------|
| `auto_approve_under` | integer | Auto-approve orders under this amount (JPY) |
| `allowed_categories` | string[] | Allowed categories (empty = all) |
| `max_orders_per_day` | integer | Daily order limit |
| `max_items_per_order` | integer | Max product types per order |
| `require_dry_run` | boolean | Require dry-run before real order |

## Key Design Principles

- **Agent-First**: All endpoints optimized for LLM consumption
- **Policy control**: Agent behavior scoped per API key
- **dry_run support**: Simulate orders before committing (`dry_run: true`)
- **agent_hint**: All responses include hints for LLM next-action decisions

## Development Roadmap

| Week | Focus |
|------|-------|
| 1 | DB schema + Alembic migrations + Product CRUD |
| 2 | Search API + API key auth middleware |
| 3 | Order API + Policy engine |
| 4 | Admin UI (products, API keys, policies) |
| 5 | Railway deployment + integration tests |
| 6 | Demo agent (Claude/GPT ordering via the API) |

## Deployment (Railway)

```toml
# railway.toml
[build]
builder = "DOCKERFILE"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
```

Push to GitHub → auto-deploys to Railway.
