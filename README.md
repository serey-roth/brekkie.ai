# brekkie.ai

AI meal planning assistant with multi-turn conversations. Built with FastAPI, LangGraph, React and Supabase.

**Live**: [brekkie-ai.vercel.app](https://brekkie-ai.vercel.app)

## Structure

- **`/backend`** — FastAPI service with LangGraph AI agent, PostgreSQL persistence, and WebSocket chat
- **`/frontend/web`** — React app with real-time chat interface and recipe display

## Tech Stack

**Backend** — Python 3.12, FastAPI, LangChain, LangGraph, Google Generative AI, PostgreSQL (Supabase), Poetry

**Frontend** — React 19, TypeScript, Vite, Tailwind CSS, Supabase Auth, pnpm

## Quick Start

### Backend

```bash
cd backend
poetry install
cp .env.example .env.development  # configure env vars
alembic upgrade head
poetry run uvicorn api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend/web
pnpm install
cp .env.example .env.development  # configure env vars
pnpm dev
```

See [backend/README.md](backend/README.md) and [frontend/web/README.md](frontend/web/README.md) for full setup details.

## Deployment

- **Backend** → [Render](https://render.com) (Docker container via `render.yaml`)
- **Frontend** → [Vercel](https://vercel.com) (root directory: `frontend/web`)
