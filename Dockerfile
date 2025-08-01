# =========================
# Frontend Build Stage
# =========================
FROM node:22-alpine AS frontend-builder

# Set build-time variables
ARG VITE_API_BASE_URL
ARG VITE_WS_BASE_URL
ARG VITE_SUPABASE_URL
ARG VITE_ENVIRONMENT
ARG MODE

# Set environment variables so Vite can use them
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_BASE_URL=$VITE_WS_BASE_URL
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_ENVIRONMENT=$VITE_ENVIRONMENT
ENV MODE=$MODE

# Install pnpm
RUN npm install -g pnpm

WORKDIR /app/frontend

# Install deps
COPY frontend/web/package.json frontend/web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Copy frontend source
COPY frontend/web/ ./

# Build with explicit mode
RUN if [ "$MODE" = "staging" ]; then pnpm build --mode staging; else pnpm build; fi

# =========================
# Backend Build Stage
# =========================
FROM python:3.12-alpine AS backend-builder

# Install build dependencies for psycopg which is needed for sqlalchemy
RUN apk add --no-cache \
    postgresql-dev \
    gcc \
    musl-dev \
    python3-dev

RUN pip install poetry

WORKDIR /app/backend

COPY backend/pyproject.toml backend/poetry.lock ./
COPY backend/README.md ./
COPY backend/ ./

RUN poetry config virtualenvs.create false
RUN poetry install --only=main --no-interaction --no-ansi

# DEBUG: Confirm psycopg installed and built
RUN pip show psycopg

# =========================
# Final Runtime Stage
# =========================
FROM python:3.12-alpine

# Runtime deps for psycopg
RUN apk add --no-cache postgresql-libs

WORKDIR /app

COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin
COPY --from=backend-builder /app/backend /app/backend
COPY --from=frontend-builder /app/frontend/dist /app/backend/src/frontend/dist

WORKDIR /app/backend/src
ENV PYTHONPATH=/app/backend/src

# Make the startup script executable
RUN chmod +x /app/backend/start.sh

EXPOSE 8080
CMD ["/app/backend/start.sh"]
