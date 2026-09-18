FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir poetry==1.8.3

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true \
    && poetry install --no-root --only main --no-interaction --no-ansi

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

FROM python:3.12-slim AS runtime

WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "app.bot.main"]
