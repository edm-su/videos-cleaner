FROM ghcr.io/astral-sh/uv:python3.13-alpine

ENV UV_COMPILE_BYTECODE=1

ADD . /app

WORKDIR /app
RUN uv sync --locked --no-dev

CMD ["uv", "run", "cleaner"]
