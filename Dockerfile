FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY app ./app

RUN uv sync --frozen --no-dev \
    && useradd --create-home --uid 10001 app \
    && mkdir -p /app/storage \
    && chown -R app:app /app

COPY --chown=app:app data/docs ./data/docs

ENV PATH="/app/.venv/bin:${PATH}"

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
