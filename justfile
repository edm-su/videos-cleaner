lint:
    uv run ruff check
    uv run ruff format --check

type-check:
    uv run pyrefly check .
