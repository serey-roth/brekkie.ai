# brekkie.ai Backend

FastAPI backend for brekkie.ai — an AI meal planning assistant with multi-turn conversations.

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **AI**: LangChain, LangGraph, Google Generative AI
- **Database**: PostgreSQL (Supabase) with SQLAlchemy and Alembic
- **Auth**: Supabase JWT (verified via JWKS)
- **Package Manager**: Poetry

## Project Structure

```text
src/
├── ai/                    # AI agent implementation
├── api/                   # FastAPI routes and dependency injection
│   ├── main.py
│   ├── deps.py
│   └── routes/
├── database/              # DB connection and checkpointer
├── repositories/          # Data access layer
├── schemas/               # Pydantic models
├── services/
│   ├── ai_food_agent/     # Google AI agent
│   ├── chat_services/     # Chat session orchestration
│   ├── data_services/     # Business logic
│   └── streaming_recipe_parser/
└── utils/
```

## API Endpoints

- `POST /api/auth/verify-jwt` — verify Supabase JWT, create or update user
- `GET /api/threads` — get user's chat threads
- `GET /api/threads/{id}/messages` — get messages for a thread
- `GET /api/recipes` — get user's saved recipes
- `WS /ws` — real-time chat WebSocket (auth via `?token=`)
- `GET /api/health` — health check

## Development

### Prerequisites

- Python 3.12+
- Poetry
- PostgreSQL

### Setup

1. Install dependencies:

   ```bash
   poetry install
   ```

2. Copy and configure environment variables:

   ```bash
   cp .env.example .env.development
   ```

   Required variables:
   - `DB_URL` — `postgresql+psycopg://...`
   - `CHECKPOINT_DB_URL` — `postgresql://...`
   - `GOOGLE_API_KEY`
   - `SUPABASE_URL`
   - `ALLOWED_ORIGINS` — comma-separated list of allowed frontend origins

3. Run migrations:

   ```bash
   alembic upgrade head
   ```

4. Start the server:

   ```bash
   poetry run uvicorn api.main:app --reload --port 8000
   ```

### Code Quality

```bash
poetry run mypy src/
poetry run ruff check src/
poetry run ruff format src/
```

## Deployment

Deployed to [Render](https://render.com) as a Docker container. Configuration is in `render.yaml` at the repo root.
