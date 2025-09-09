lint:
    uv run ruff check
    uv run ruff format --check

format:
    uv run ruff format

type-check:
    uv run pyrefly check .

unit-tests:
    uv run pytest .
