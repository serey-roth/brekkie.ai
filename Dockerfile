# =========================
# Build
# =========================
FROM python:3.12-alpine AS backend-builder

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

# =========================
# Final Runtime
# =========================
FROM python:3.12-alpine

RUN apk add --no-cache postgresql-libs

WORKDIR /app

COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin
COPY --from=backend-builder /app/backend /app/backend

WORKDIR /app/backend/src
ENV PYTHONPATH=/app/backend/src

RUN chmod +x /app/backend/start.sh

EXPOSE 8080
CMD ["/app/backend/start.sh"]
