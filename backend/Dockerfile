FROM ghcr.io/astral-sh/uv:0.12.5-python3.12-alpine3.23 AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apk add --no-cache build-base libffi-dev zlib-dev

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY pyproject.toml uv.lock ./
COPY backend/ ./backend/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

RUN uv run --with pyinstaller pyinstaller \
    --onefile backend/main.py \
    --name main \
    --paths . \
    --collect-submodules uvicorn \
    --hidden-import sqlite3 \
    --hidden-import sqlalchemy.dialects.sqlite \
    --copy-metadata email-validator \
    --copy-metadata pydantic


FROM alpine:3.23

WORKDIR /app

RUN apk add --no-cache libgcc \
    && addgroup -S appuser \
    && adduser -S -G appuser -h /app appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data

COPY --from=builder --chown=appuser:appuser /app/dist/main /app/main

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/main"]