
FROM python:3.13-slim@sha256:739e7213785e88c0f702dcdc12c0973afcbd606dbf021a589cab77d6b00b579d AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:90bbb3c16635e9627f49eec6539f956d70746c409209041800a0280b93152823 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN useradd -u 10001 -m appuser

WORKDIR /home/appuser/app

ENV PATH="/home/appuser/app/.venv/bin:${PATH}"

COPY pyproject.toml .
COPY uv.lock .


FROM base AS dev
RUN uv sync --frozen --no-install-project
COPY .trivyignore /
COPY src/ ./src/
COPY tests/ ./tests/
RUN uv sync --frozen
USER 10001
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "-k", "uvicorn.workers.UvicornWorker", "src.main:app"]

FROM base AS runtime
RUN uv sync --frozen --no-dev --no-install-project
COPY .trivyignore /
COPY src/ ./src/
RUN uv sync --frozen --no-dev
USER 10001
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "-k", "uvicorn.workers.UvicornWorker", "src.main:app"]

